// ==============================================================================
// 0. MAPEOS Y CONSTANTES
// ==============================================================================

// Mapeo de complejidad a peso para Actores (Tabla 2)
const ACTOR_WEIGHT_MAP = {
    "Simple": 1,
    "Medio": 2,
    "Complejo": 3,
    "Selecciona": 0
};

// Pesos de los factores técnicos T1 a T13 (Tabla 3)
const technicalFactorsWeights = [
    2,   // T1
    1,   // T2
    1,   // T3
    1,   // T4
    1,   // T5
    0.5, // T6
    0.5, // T7
    2,   // T8
    1,   // T9
    1,   // T10
    1,   // T11
    1,   // T12
    1    // T13
];

// Pesos de los factores ambientales E1 a E8 (Tabla 4)
const environmentFactorsWeights = [
    1.5, // E1
    0.5, // E2
    1,   // E3
    0.5, // E4
    1,   // E5 (Motivación)  ← CORREGIDO: 1
    2,   // E6
    -1,  // E7
    -1   // E8
];

// --- Versionado para invalidar cache cuando cambian pesos/logic ----
const UCP_SCHEMA_VERSION = '2025-11-08-ef-weights-v2';
(function ensureSchemaVersion(){
    const cur = localStorage.getItem('UCP_SCHEMA_VERSION');
    if (cur !== UCP_SCHEMA_VERSION) {
        // Limpia solo claves de EF para recalcular con nuevos pesos
        for (let i = 1; i <= 8; i++) {
            localStorage.removeItem(`ImpactEf${i}`);
            localStorage.removeItem(`EvaEf${i}`);
        }
        localStorage.removeItem('totalImpactEfValue');
        localStorage.removeItem('totalCountEfValue');
        localStorage.removeItem('faValue');
        // También conviene recalcular T por si hubieran cambiado (no es el caso, pero seguro)
        for (let i = 1; i <= 13; i++) {
            localStorage.removeItem(`ImpactT${i}`);
            localStorage.removeItem(`EvaT${i}`);
        }
        localStorage.removeItem('totalTF');
        localStorage.removeItem('tcfValue');
        // UCP/Esfuerzo derivados
        localStorage.removeItem('ucpValue');
        localStorage.removeItem('esfuerzoE');
        localStorage.removeItem('totalHoras');
        localStorage.removeItem('totalHP');

        localStorage.setItem('UCP_SCHEMA_VERSION', UCP_SCHEMA_VERSION);
    }
})();

// ==============================================================================
// 1. FUNCIONES PRINCIPALES DE INICIALIZACIÓN Y LIMPIEZA
// ==============================================================================

window.onload = () => {
    // 1. Cargar datos de tablas dinámicas (Actores y Casos de Uso)
    loadTableData1();
    loadTableData2();

    // 2. Cargar datos de tablas estáticas con selects (Factores T y E)
    loadTableData3();
    loadTableData4(); // ← recalcula impactos EF con pesos actuales

    // 3. Cargar y calcular los totales intermedios y finales
    updateTotalImpact();    // TF → TCF
    updateTotalImpactEf();  // EF → FA

    // 4. Inicializar Horas/Persona (usa Esfuerzo)
    loadHorasPersonaTable();

    // 5. Forzar cálculo final
    calcularUCP();
    calcularEsfuerzo();
};

function clearData() {
    if (confirm("¿Estás seguro de que deseas limpiar TODOS los datos de la calculadora?")) {
        localStorage.clear();
        location.reload();
    }
}

// ==============================================================================
// 2. CÁLCULO DE CASOS DE USO Y ACTORES (PCU & PA)
// ==============================================================================

function updateUUCP() {
    const totalProduct  = parseFloat(document.getElementById("totalProduct").textContent)  || 0;
    const totalProduct2 = parseFloat(document.getElementById("totalProduct2").textContent) || 0;
    const uucpTotal = totalProduct + totalProduct2;

    document.getElementById("PA").textContent   = totalProduct.toFixed(0);
    document.getElementById("PCU").textContent  = totalProduct2.toFixed(0);
    document.getElementById("uucp").textContent = uucpTotal.toFixed(0);

    calcularUCP();
}

// ---- Tabla 1: Casos de Uso (PCU)
function determineComplexity(transacciones) {
    if (transacciones >= 8) {
        return { complejidad: "Complejo", peso: 15 };
    } else if (transacciones >= 4 && transacciones <= 7) {
        return { complejidad: "Medio", peso: 10 };
    } else if (transacciones >= 1 && transacciones <= 3) {
        return { complejidad: "Simple", peso: 5 };
    } else {
        return { complejidad: "N/A", peso: 0 };
    }
}

function saveTableData1() {
    const rows = Array.from(document.querySelectorAll("#actorsTable1 tbody tr")).map(row => {
        return {
            casoUso: row.cells[0].textContent,
            transacciones: row.cells[1].querySelector("input") ? row.cells[1].querySelector("input").value : '0',
            complejidad: row.cells[2].textContent,
            peso: row.cells[3].textContent,
            producto: row.cells[4].textContent
        };
    });
    localStorage.setItem("tableData1", JSON.stringify(rows));
}

function calculateProduct(element) {
    const row = element.closest('tr');

    const transacciones = parseInt(row.cells[1].querySelector("input").value) || 0;

    const { complejidad, peso } = determineComplexity(transacciones);

    row.cells[2].textContent = complejidad;
    row.cells[3].textContent = peso.toFixed(0);
    row.cells[4].textContent = peso.toFixed(0);

    calculateTotal();
    saveTableData1();
}

function calculateTotal() {
    const tableBody = document.querySelector("#actorsTable1 tbody");
    let total = 0;
    Array.from(tableBody.rows).forEach(row => {
        total += parseFloat(row.cells[4].textContent) || 0;
    });
    document.getElementById("totalProduct").textContent = total.toFixed(0);
    updateUUCP();
}

function addRow1() {
    const tableBody = document.querySelector("#actorsTable1 tbody");
    const newRow = tableBody.insertRow();

    const rowUpdateHandler = (element) => {
        calculateProduct(element);
        saveTableData1();
    };

    const cellCaso = newRow.insertCell();
    cellCaso.contentEditable = "true";
    cellCaso.oninput = saveTableData1;

    const cellTransacciones = newRow.insertCell();
    const inputTransacciones = document.createElement("input");
    inputTransacciones.type = "number";
    inputTransacciones.min = "0";
    inputTransacciones.value = "0";
    inputTransacciones.className = "form-control form-control-sm text-center";
    inputTransacciones.oninput = () => rowUpdateHandler(inputTransacciones);
    cellTransacciones.appendChild(inputTransacciones);

    const cellComplejidad = newRow.insertCell();
    cellComplejidad.textContent = 'N/A';
    cellComplejidad.style.fontWeight = 'normal';

    const cellPeso = newRow.insertCell();
    cellPeso.textContent = '0';
    cellPeso.style.fontWeight = 'bold';

    const cellProducto = newRow.insertCell();
    cellProducto.textContent = '0';
    cellProducto.style.fontWeight = 'bold';

    saveTableData1();
}

function deleteLastRow1() {
    const tableBody = document.querySelector("#actorsTable1 tbody");
    if (tableBody.rows.length > 0) {
        tableBody.deleteRow(tableBody.rows.length - 1);
        calculateTotal();
        saveTableData1();
    }
}

function loadTableData1() {
    const rowsData = JSON.parse(localStorage.getItem("tableData1")) || [];
    const tableBody = document.querySelector("#actorsTable1 tbody");
    tableBody.innerHTML = "";

    rowsData.forEach(data => {
        const newRow = tableBody.insertRow();

        const cellCaso = newRow.insertCell();
        cellCaso.contentEditable = "true";
        cellCaso.textContent = data.casoUso;
        cellCaso.oninput = saveTableData1;

        const cellTransacciones = newRow.insertCell();
        const inputTransacciones = document.createElement("input");
        inputTransacciones.type = "number";
        inputTransacciones.min = "0";
        inputTransacciones.value = data.transacciones;
        inputTransacciones.className = "form-control form-control-sm text-center";
        inputTransacciones.oninput = () => { calculateProduct(inputTransacciones); saveTableData1(); };
        cellTransacciones.appendChild(inputTransacciones);

        const cellComplejidad = newRow.insertCell();
        cellComplejidad.textContent = data.complejidad;
        cellComplejidad.style.fontWeight = 'normal';

        const cellPeso = newRow.insertCell();
        cellPeso.textContent = data.peso;
        cellPeso.style.fontWeight = 'bold';

        const cellProducto = newRow.insertCell();
        cellProducto.textContent = data.producto;
        cellProducto.style.fontWeight = 'bold';
    });
    calculateTotal();
}

// ---- Tabla 2: Actores (PA)
function saveTableData2() {
    const rows = Array.from(document.querySelectorAll("#actorsTable2 tbody tr")).map(row => {
        return {
            actores: row.cells[0].textContent,
            tipoActor: row.cells[1].querySelector("select") ? row.cells[1].querySelector("select").value : 'Selecciona',
            peso: row.cells[2].textContent,
            producto: row.cells[3].textContent
        };
    });
    localStorage.setItem("tableData2", JSON.stringify(rows));
}

function calculateProduct2(element) {
    const row = element.closest('tr');

    const tipoActor = row.cells[1].querySelector("select").value;
    const peso = ACTOR_WEIGHT_MAP[tipoActor] || 0;

    row.cells[2].textContent = peso.toFixed(0);
    row.cells[3].textContent = peso.toFixed(0);

    calculateTotal2();
    saveTableData2();
}

function calculateTotal2() {
    const tableBody = document.querySelector("#actorsTable2 tbody");
    let total = 0;
    Array.from(tableBody.rows).forEach(row => {
        total += parseFloat(row.cells[3].textContent) || 0;
    });
    document.getElementById("totalProduct2").textContent = total.toFixed(0);
    updateUUCP();
}

function addRow2() {
    const tableBody = document.querySelector("#actorsTable2 tbody");
    const newRow = tableBody.insertRow();

    const rowUpdateHandler = (element) => {
        calculateProduct2(element);
        saveTableData2();
    };

    const cellActores = newRow.insertCell();
    cellActores.contentEditable = "true";
    cellActores.oninput = saveTableData2;

    const cellTipoActor = newRow.insertCell();
    const selectTipoActor = document.createElement("select");
    selectTipoActor.className = "form-select form-select-sm";
    ["Selecciona","Simple", "Medio", "Complejo"].forEach(optionText => {
        const option = document.createElement("option");
        option.value = optionText;
        option.text = optionText;
        selectTipoActor.appendChild(option);
    });
    selectTipoActor.onchange = () => rowUpdateHandler(selectTipoActor);
    cellTipoActor.appendChild(selectTipoActor);

    const cellPeso = newRow.insertCell();
    cellPeso.textContent = '0';
    cellPeso.style.fontWeight = 'bold';

    const cellProducto = newRow.insertCell();
    cellProducto.textContent = '0';
    cellProducto.style.fontWeight = 'bold';

    saveTableData2();
}

function deleteLastRow2() {
    const tableBody = document.querySelector("#actorsTable2 tbody");
    if (tableBody.rows.length > 0) {
        tableBody.deleteRow(tableBody.rows.length - 1);
        calculateTotal2();
        saveTableData2();
    }
}

function loadTableData2() {
    const rowsData = JSON.parse(localStorage.getItem("tableData2")) || [];
    const tableBody = document.querySelector("#actorsTable2 tbody");
    tableBody.innerHTML = "";

    rowsData.forEach(data => {
        const newRow = tableBody.insertRow();

        const cellActores = newRow.insertCell();
        cellActores.contentEditable = "true";
        cellActores.textContent = data.actores;
        cellActores.oninput = saveTableData2;

        const cellTipoActor = newRow.insertCell();
        const selectTipoActor = document.createElement("select");
        selectTipoActor.className = "form-select form-select-sm";
        ["Selecciona","Simple", "Medio", "Complejo"].forEach(optionText => {
            const option = document.createElement("option");
            option.value = optionText;
            option.text = optionText;
            if (optionText === data.tipoActor) option.selected = true;
            selectTipoActor.appendChild(option);
        });
        selectTipoActor.onchange = () => { calculateProduct2(selectTipoActor); saveTableData2(); };
        cellTipoActor.appendChild(selectTipoActor);

        const cellPeso = newRow.insertCell();
        cellPeso.textContent = data.peso;
        cellPeso.style.fontWeight = 'bold';

        const cellProducto = newRow.insertCell();
        cellProducto.textContent = data.producto;
        cellProducto.style.fontWeight = 'bold';
    });
    calculateTotal2();
}

// ==============================================================================
// 3. FACTORES TÉCNICOS (TF & TCF)
// ==============================================================================

function calculateImpactT(index, selectedValue) {
    const multiplier = technicalFactorsWeights[index - 1];
    const impact = selectedValue * multiplier;

    document.getElementById(`ImT${index}`).textContent = impact.toFixed(2);
    localStorage.setItem(`ImpactT${index}`, impact.toFixed(3));
    localStorage.setItem(`EvaT${index}`, selectedValue);

    updateTotalImpact();
}

function updateTotalImpact() {
    let totalImpact = 0;

    for (let i = 1; i <= technicalFactorsWeights.length; i++) {
        const impactValue = parseFloat(localStorage.getItem(`ImpactT${i}`)) || 0;
        totalImpact += impactValue;
    }

    document.getElementById("totalTF").textContent = totalImpact.toFixed(2);
    localStorage.setItem("totalTF", totalImpact.toFixed(3));

    calcularTCF(totalImpact);
}

function calcularTCF(totalTF = null) {
    if (totalTF === null) {
        totalTF = parseFloat(localStorage.getItem("totalTF")) || 0;
    }
    const tcf = 0.6 + (totalTF * 0.01);

    document.getElementById("tcf").textContent = tcf.toFixed(2);
    localStorage.setItem("tcfValue", tcf.toFixed(3));

    calcularUCP();
}

function loadTableData3() {
    const tcfValue = parseFloat(localStorage.getItem("tcfValue")) || 0;
    document.getElementById("tcf").textContent = tcfValue.toFixed(2);

    for (let i = 1; i <= technicalFactorsWeights.length; i++) {
        const evaluationCell = document.getElementById(`EvaT${i}`);

        const select = document.createElement('select');
        select.className = "form-select form-select-sm";
        select.innerHTML = `
            <option value="">Selecciona</option>
            <option value="0">0</option>
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="4">4</option>
            <option value="5">5</option>
        `;

        const savedValue = localStorage.getItem(`EvaT${i}`);
        if (savedValue) {
            select.value = savedValue;
            document.getElementById(`ImT${i}`).textContent = parseFloat(localStorage.getItem(`ImpactT${i}`) || 0).toFixed(2);
        }

        select.addEventListener('change', function() {
            const selectedValue = parseInt(this.value);
            if (!isNaN(selectedValue)) {
                calculateImpactT(i, selectedValue);
            } else {
                document.getElementById(`ImT${i}`).textContent = '0.00';
                localStorage.removeItem(`EvaT${i}`);
                localStorage.setItem(`ImpactT${i}`, '0.000');
                updateTotalImpact();
            }
        });

        evaluationCell.appendChild(select);
    }
}

// ==============================================================================
// 4. FACTORES AMBIENTALES (EF & FA)
// ==============================================================================

function calculateImpactEf(index, selectedValue) {
    const multiplier = environmentFactorsWeights[index - 1];
    const impact = selectedValue * multiplier;

    document.getElementById(`ImEf${index}`).textContent = impact.toFixed(2);
    localStorage.setItem(`ImpactEf${index}`, impact.toFixed(3));
    localStorage.setItem(`EvaEf${index}`, selectedValue);

    updateTotalImpactEf();
}

/**
 * Calcula y guarda: 
 *  - totalImpactEF (suma ponderada para FA)
 *  - totalCountEF (conteo para determinar CF)
 */
function updateTotalImpactEf() {
    let totalImpactEF = 0;
    let totalCountEF = 0;

    for (let i = 1; i <= environmentFactorsWeights.length; i++) {
        const evaluationValue = parseFloat(localStorage.getItem(`EvaEf${i}`)) || 0;
        const impactValue = parseFloat(localStorage.getItem(`ImpactEf${i}`)) || 0;

        totalImpactEF += impactValue;

        if (evaluationValue !== 0) {
            if (i >= 1 && i <= 6) {
                if (evaluationValue < 3) totalCountEF += 1;
            } else if (i >= 7 && i <= 8) {
                if (evaluationValue > 3) totalCountEF += 1;
            }
        }
    }

    document.getElementById("totalEf").textContent = totalImpactEF.toFixed(2);
    localStorage.setItem("totalImpactEfValue", totalImpactEF.toFixed(3));

    localStorage.setItem("totalCountEfValue", totalCountEF.toFixed(0));

    calcularEF(totalImpactEF);
}

function calcularEF(totalImpact = null) {
    if (totalImpact === null) {
        totalImpact = parseFloat(localStorage.getItem("totalImpactEfValue")) || 0;
    }
    const fa = 1.4 + (-0.03 * totalImpact);

    document.getElementById("totalEF").textContent = fa.toFixed(2);
    localStorage.setItem("faValue", fa.toFixed(3));

    calcularUCP();
}

// ← CLAVE: recargar EF con recálculo usando pesos actuales (E5=1)
function loadTableData4() {
    // Mostrar FA guardado (solo visual al inicio)
    const faValue = parseFloat(localStorage.getItem("faValue")) || 0;
    document.getElementById("totalEF").textContent = faValue.toFixed(2);

    for (let i = 1; i <= environmentFactorsWeights.length; i++) {
        const evaluationCell = document.getElementById(`EvaEf${i}`);

        const select = document.createElement('select');
        select.className = "form-select form-select-sm";
        select.innerHTML = `
            <option value="">Selecciona</option>
            <option value="0">0</option>
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="4">4</option>
            <option value="5">5</option>
        `;

        const savedValue = localStorage.getItem(`EvaEf${i}`);
        if (savedValue !== null && savedValue !== "") {
            select.value = savedValue;
            // Recalcula impacto con PESO ACTUAL (no uses ImpactEf viejo)
            calculateImpactEf(i, parseInt(savedValue));
        } else {
            document.getElementById(`ImEf${i}`).textContent = '0.00';
            localStorage.setItem(`ImpactEf${i}`, '0.000');
        }

        select.addEventListener('change', function() {
            const selectedValue = parseInt(this.value);
            if (!isNaN(selectedValue)) {
                calculateImpactEf(i, selectedValue);
            } else {
                document.getElementById(`ImEf${i}`).textContent = '0.00';
                localStorage.removeItem(`EvaEf${i}`);
                localStorage.setItem(`ImpactEf${i}`, '0.000');
                updateTotalImpactEf();
            }
        });

        evaluationCell.appendChild(select);
    }

    // Asegura totales con los impactos recalculados
    updateTotalImpactEf();
}

// ==============================================================================
// 5. CÁLCULO DE UCP AJUSTADO Y ESFUERZO (E)
// ==============================================================================

function calcularUCP() {
    const UUCP = parseFloat(document.getElementById("uucp").textContent) || 0;
    const TCF  = parseFloat(localStorage.getItem("tcfValue")) || 0;
    const FA   = parseFloat(localStorage.getItem("faValue"))  || 0;

    const UCP = UUCP * TCF * FA;

    document.getElementById("ttuucp").textContent = UUCP.toFixed(0);
    document.getElementById("tttcf").textContent  = TCF.toFixed(2);
    document.getElementById("ttef").textContent   = FA.toFixed(2);
    document.getElementById("ttucp").textContent  = UCP.toFixed(2);

    localStorage.setItem("ucpValue", UCP.toFixed(3));

    calcularEsfuerzo();
}

function calcularCFAutomatica() {
    const totalConteo = parseFloat(localStorage.getItem("totalCountEfValue")) || 0;

    let CF = 0;
    if (totalConteo <= 2) {
        CF = 20;
    } else if (totalConteo > 2 && totalConteo <= 4) {
        CF = 28;
    } else if (totalConteo > 4) {
        CF = 36;
    }

    localStorage.setItem("calculatedCF", CF.toFixed(0));
    return CF;
}

function calcularEsfuerzo() {
    const cfValue  = calcularCFAutomatica();
    const ucpValue = parseFloat(localStorage.getItem("ucpValue")) || 0;

    const esfuerzoE = cfValue * ucpValue;

    document.getElementById("ttCF").textContent  = cfValue.toFixed(0);
    document.getElementById("tttUCP").textContent = ucpValue.toFixed(2);
    document.getElementById("ttE").textContent    = esfuerzoE.toFixed(2);

    localStorage.setItem("esfuerzoE", esfuerzoE.toFixed(3));

    calcularTotalesEsfuerzo(esfuerzoE);

    const ehCell = document.getElementById("eh");
    if (ehCell) {
        ehCell.textContent = esfuerzoE.toFixed(2);
        calcularTotalHorasPersona();
    }
}

function calcularTotalesEsfuerzo(esfuerzoE) {
    const totalHoras   = esfuerzoE;
    const totalSemanas = totalHoras / 40;
    const totalMeses   = totalSemanas / 4.333;

    document.getElementById("tth").textContent = totalHoras.toFixed(2);
    document.getElementById("tts").textContent = totalSemanas.toFixed(2);
    document.getElementById("ttm").textContent = totalMeses.toFixed(2);

    localStorage.setItem("totalHoras", totalHoras.toFixed(3));
}

// ==============================================================================
// 6. HORAS / PERSONA
// ==============================================================================

function loadHorasPersonaTable() {
    const emCell = document.getElementById("em");

    let emInput = document.getElementById('inputEm');
    if (!emInput) {
        emInput = document.createElement('input');
        emInput.type = 'number';
        emInput.id = 'inputEm';
        emInput.min = 1;
        emInput.placeholder = '1';
        emInput.className = 'form-control form-control-sm';
        emInput.style = 'text-align: center;';

        emInput.value = localStorage.getItem("emValue") || "";

        emInput.addEventListener('input', function() {
            localStorage.setItem("emValue", emInput.value);
            calcularTotalHorasPersona();
        });

        emCell.innerHTML = '';
        emCell.appendChild(emInput);
    }

    document.getElementById("eh").textContent   = parseFloat(localStorage.getItem("esfuerzoE") || 0).toFixed(2);
    document.getElementById("temh").textContent = parseFloat(localStorage.getItem("totalHP")   || 0).toFixed(2);

    calcularTotalHorasPersona();
}

function calcularTotalHorasPersona() {
    const ehValue = parseFloat(localStorage.getItem("esfuerzoE")) || 0;
    const emInput = document.getElementById("inputEm");

    const emValue = parseFloat(emInput ? emInput.value : 1) || 1;

    const totalHP = ehValue / emValue;

    document.getElementById("temh").textContent = totalHP.toFixed(2);
    localStorage.setItem("totalHP", totalHP.toFixed(3));
}
