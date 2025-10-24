// ==============================================================================
// 0. MAPEOS Y CONSTANTES
// ==============================================================================

// Mapeo de complejidad a peso para Actores (Tabla 2) - Se mantiene
const ACTOR_WEIGHT_MAP = {
    "Simple": 1,
    "Medio": 2,
    "Complejo": 3,
    "Selecciona": 0
};

// Pesos de los factores técnicos T1 a T13 (Tabla 3) - Pesos corregidos
const technicalFactorsWeights = [
    2,   // T1
    1,   // T2. CORREGIDO: Objetivos de rendimiento vale 1.
    1,   // T3
    1,   // T4
    1,   // T5
    0.5, // T6
    0.5, // T7
    2,   // T8
    1,   // T9
    1,   // T10
    1,   // T11
    1,   // T12
    1    // T13
];

// Pesos de los factores ambientales E1 a E8 (Tabla 4) - Pesos corregidos
const environmentFactorsWeights = [
    1.5, // E1
    0.5, // E2
    1,   // E3
    0.5, // E4
    0.5, // E5. CORREGIDO: Motivación vale 0.5.
    2,   // E6
    -1,  // E7
    -1   // E8
];


// ==============================================================================
// 1. FUNCIONES PRINCIPALES DE INICIALIZACIÓN Y LIMPIEZA
// ==============================================================================

// Función de inicialización al cargar la página
window.onload = () => {
    // 1. Cargar datos de tablas dinámicas (Actores y Casos de Uso)
    loadTableData1();
    loadTableData2();

    // 2. Cargar datos de tablas estáticas con selects (Factores T y E)
    loadTableData3();
    loadTableData4();

    // 3. Cargar y calcular los totales intermedios y finales
    updateTotalImpact();
    updateTotalImpactEf(); // ¡Calcula Impacto Ponderado Y Conteo!

    // 4. Inicializar la tabla de Horas/Persona (debe ir al final para obtener los datos de Esfuerzo)
    loadHorasPersonaTable();

    // Asegurar que el cálculo final de UCP y Esfuerzo se ejecute al cargar:
    calcularUCP();
    calcularEsfuerzo();
};

// Función para limpiar todo el localStorage y recargar la página
function clearData() {
    if (confirm("¿Estás seguro de que deseas limpiar TODOS los datos de la calculadora?")) {
        localStorage.clear();
        location.reload();
    }
}

// ==============================================================================
// 2. CÁLCULO DE CASOS DE USO Y ACTORES (PCU & PA)
// ==============================================================================

// Actualiza la celda UUCP (Unadjusted Use Case Points = PA + PCU)
function updateUUCP() {
    const totalProduct = parseFloat(document.getElementById("totalProduct").textContent) || 0;
    const totalProduct2 = parseFloat(document.getElementById("totalProduct2").textContent) || 0;
    const uucpTotal = totalProduct + totalProduct2;

    document.getElementById("PA").textContent = totalProduct.toFixed(0);
    document.getElementById("PCU").textContent = totalProduct2.toFixed(0);
    document.getElementById("uucp").textContent = uucpTotal.toFixed(0);

    // Activar el cálculo del UCP ajustado después de cambiar el UUCP
    calcularUCP();
}

// ---------------------- Funciones para Tabla 1: Casos de Uso (PCU) ----------------------

/**
 * Determina la complejidad y el peso de un Caso de Uso basado en el número de transacciones.
 * @param {number} transacciones - El número de transacciones.
 * @returns {{complejidad: string, peso: number}}
 */
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
    // La estructura de la fila es: CasoUso (0), Transacciones (1), Complejidad (2), Peso (3), Producto (4)
    const rows = Array.from(document.querySelectorAll("#actorsTable1 tbody tr")).map(row => {
        return {
            casoUso: row.cells[0].textContent,
            transacciones: row.cells[1].querySelector("input") ? row.cells[1].querySelector("input").value : '0',
            complejidad: row.cells[2].textContent,
            peso: row.cells[3].textContent,
            producto: row.cells[4].textContent // Ahora Producto está en la celda 4
        };
    });
    localStorage.setItem("tableData1", JSON.stringify(rows));
}

function calculateProduct(element) {
    const row = element.closest('tr');
    
    // 1. Obtener las transacciones
    const transacciones = parseInt(row.cells[1].querySelector("input").value) || 0;
    
    // 2. Determinar la complejidad y el peso
    const { complejidad, peso } = determineComplexity(transacciones);
    
    // 3. Actualizar la celda de Complejidad (Celda 2)
    row.cells[2].textContent = complejidad;
    
    // 4. Actualizar la celda de Peso (Celda 3)
    row.cells[3].textContent = peso.toFixed(0);
    
    // 5. El producto es igual al Peso (ya que cantidad=1)
    const producto = peso;
    
    // 6. Actualizar la celda de Producto (Celda 4)
    row.cells[4].textContent = producto.toFixed(0);

    calculateTotal();
    saveTableData1();
}

function calculateTotal() {
    const tableBody = document.querySelector("#actorsTable1 tbody");
    let total = 0;
    Array.from(tableBody.rows).forEach(row => {
        // Sumamos el valor de la celda de Producto (índice 4)
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

    // Celda 0: Caso de Uso
    const cellCaso = newRow.insertCell();
    cellCaso.contentEditable = "true";
    cellCaso.oninput = saveTableData1;

    // Celda 1: Transacciones (Input numérico)
    const cellTransacciones = newRow.insertCell();
    const inputTransacciones = document.createElement("input");
    inputTransacciones.type = "number";
    inputTransacciones.min = "0";
    inputTransacciones.value = "0";
    inputTransacciones.className = "form-control form-control-sm text-center";
    inputTransacciones.oninput = () => rowUpdateHandler(inputTransacciones);
    cellTransacciones.appendChild(inputTransacciones);

    // Celda 2: Complejidad (Solo Lectura, actualizado por Transacciones)
    const cellComplejidad = newRow.insertCell();
    cellComplejidad.textContent = 'N/A';
    cellComplejidad.style.fontWeight = 'normal'; 

    // Celda 3: Peso (Solo Lectura, actualizado por Transacciones)
    const cellPeso = newRow.insertCell();
    cellPeso.textContent = '0';
    cellPeso.style.fontWeight = 'bold'; 

    // Celda 4: Producto (Solo Lectura, igual a Peso)
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
        // La nueva estructura de la fila es: CasoUso, Transacciones, Complejidad, Peso, Producto
        const newRow = tableBody.insertRow();
        
        // Celda 0: Caso de Uso
        const cellCaso = newRow.insertCell();
        cellCaso.contentEditable = "true";
        cellCaso.textContent = data.casoUso;
        cellCaso.oninput = saveTableData1;
        
        // Celda 1: Transacciones (Input numérico)
        const cellTransacciones = newRow.insertCell();
        const inputTransacciones = document.createElement("input");
        inputTransacciones.type = "number";
        inputTransacciones.min = "0";
        inputTransacciones.value = data.transacciones;
        inputTransacciones.className = "form-control form-control-sm text-center";
        inputTransacciones.oninput = () => { calculateProduct(inputTransacciones); saveTableData1(); };
        cellTransacciones.appendChild(inputTransacciones);

        // Celda 2: Complejidad (Valor calculado, solo lectura)
        const cellComplejidad = newRow.insertCell();
        cellComplejidad.textContent = data.complejidad;
        cellComplejidad.style.fontWeight = 'normal';

        // Celda 3: Peso (Valor calculado, solo lectura)
        const cellPeso = newRow.insertCell();
        cellPeso.textContent = data.peso;
        cellPeso.style.fontWeight = 'bold';

        // Celda 4: Producto (Valor calculado, solo lectura)
        const cellProducto = newRow.insertCell();
        cellProducto.textContent = data.producto;
        cellProducto.style.fontWeight = 'bold';
    });
    calculateTotal();
}

// ---------------------- Funciones para Tabla 2: Actores (PA) ----------------------
function saveTableData2() {
    // La estructura de la fila es: Actor (0), TipoActor (1), Peso (2), Producto (3)
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
    
    // 1. Obtener el Tipo de Actor y el peso asociado
    const tipoActor = row.cells[1].querySelector("select").value;
    const peso = ACTOR_WEIGHT_MAP[tipoActor] || 0;
    
    // 2. Actualizar la celda de Peso (Celda 2)
    row.cells[2].textContent = peso.toFixed(0);
    
    // 3. El producto es igual al Peso (ya que cantidad=1)
    const producto = peso;
    
    // 4. Actualizar la celda de Producto (Celda 3)
    row.cells[3].textContent = producto.toFixed(0);

    calculateTotal2();
    saveTableData2();
}

function calculateTotal2() {
    const tableBody = document.querySelector("#actorsTable2 tbody");
    let total = 0;
    Array.from(tableBody.rows).forEach(row => {
        // Sumamos el valor de la celda de Producto (índice 3)
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

    // Celda 0: Actor
    const cellActores = newRow.insertCell();
    cellActores.contentEditable = "true";
    cellActores.oninput = saveTableData2;

    // Celda 1: Tipo de Actor (Select)
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

    // Celda 2: Peso (Solo Lectura, actualizado por TipoActor)
    const cellPeso = newRow.insertCell();
    cellPeso.textContent = '0';
    cellPeso.style.fontWeight = 'bold'; 

    // Celda 3: Producto (Solo Lectura, igual a Peso)
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
        // La estructura de la fila debe ser: Actor, TipoActor, Peso, Producto
        const newRow = tableBody.insertRow();

        // Celda 0: Actor
        const cellActores = newRow.insertCell();
        cellActores.contentEditable = "true";
        cellActores.textContent = data.actores;
        cellActores.oninput = saveTableData2;

        // Celda 1: Tipo de Actor (Select)
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

        // Celda 2: Peso (Valor calculado, solo lectura)
        const cellPeso = newRow.insertCell();
        cellPeso.textContent = data.peso;
        cellPeso.style.fontWeight = 'bold';

        // Celda 3: Producto (Valor calculado, solo lectura)
        const cellProducto = newRow.insertCell();
        cellProducto.textContent = data.producto;
        cellProducto.style.fontWeight = 'bold';
    });
    calculateTotal2();
}


// ==============================================================================
// 3. FACTORES TÉCNICOS (TF & TCF)
// ==============================================================================
// Función principal de cálculo de Factores Técnicos
function calculateImpactT(index, selectedValue) {
    const multiplier = technicalFactorsWeights[index - 1];
    const impact = selectedValue * multiplier;
    
    document.getElementById(`ImT${index}`).textContent = impact.toFixed(2);
    // CAMBIO AQUÍ: Guardamos con 3 decimales para mantener precisión en el TCF total
    localStorage.setItem(`ImpactT${index}`, impact.toFixed(3)); 
    localStorage.setItem(`EvaT${index}`, selectedValue);

    updateTotalImpact();
}

// Función para calcular y mostrar la suma de todos los impactos T
function updateTotalImpact() {
    let totalImpact = 0;
    
    for (let i = 1; i <= technicalFactorsWeights.length; i++) {
        // Leemos con 3 decimales para la operación
        const impactValue = parseFloat(localStorage.getItem(`ImpactT${i}`)) || 0;
        totalImpact += impactValue;
    }

    document.getElementById("totalTF").textContent = totalImpact.toFixed(2); // Mostramos a 2 decimales
    // CAMBIO AQUÍ: Guardamos con 3 decimales para la operación de TCF
    localStorage.setItem("totalTF", totalImpact.toFixed(3)); 
    
    calcularTCF(totalImpact);
}

// Función para calcular el TCF: TCF = 0.6 + (TF * 0.01)
function calcularTCF(totalTF = null) {
    if (totalTF === null) {
        // Leemos con 3 decimales para la operación (el valor guardado)
        totalTF = parseFloat(localStorage.getItem("totalTF")) || 0;
    }
    const tcf = 0.6 + (totalTF * 0.01);
    
    document.getElementById("tcf").textContent = tcf.toFixed(2); // CAMBIO AQUÍ: Mostramos a 2 decimales
    localStorage.setItem("tcfValue", tcf.toFixed(3)); // Guardamos a 3 decimales para la operación UCP
    
    calcularUCP();
}

// Inicializa los selects en la tabla de Factores Técnicos (T)
function loadTableData3() {
    // CAMBIO AQUÍ: Leemos el valor guardado (3 decimales) y lo mostramos a 2
    const tcfValue = parseFloat(localStorage.getItem("tcfValue")) || 0;
    document.getElementById("tcf").textContent = tcfValue.toFixed(2);

    for (let i = 1; i <= technicalFactorsWeights.length; i++) {
        const evaluationCell = document.getElementById(`EvaT${i}`);
        
        // Crear un select para las evaluaciones
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
        
        // Cargar valor guardado
        const savedValue = localStorage.getItem(`EvaT${i}`);
        if (savedValue) {
            select.value = savedValue;
            // Mostramos el impacto a 2 decimales
            document.getElementById(`ImT${i}`).textContent = parseFloat(localStorage.getItem(`ImpactT${i}`) || 0).toFixed(2);
        }

        // Evento para calcular y guardar el impacto al cambiar
        select.addEventListener('change', function() {
            const selectedValue = parseInt(this.value);
            if (!isNaN(selectedValue)) {
                calculateImpactT(i, selectedValue);
            } else {
                document.getElementById(`ImT${i}`).textContent = '0.00';
                localStorage.removeItem(`EvaT${i}`);
                localStorage.setItem(`ImpactT${i}`, '0.000'); // Guardar con 3 decimales
                updateTotalImpact();
            }
        });

        evaluationCell.appendChild(select);
    }
}


// ==============================================================================
// 4. FACTORES AMBIENTALES (EF & FA)
// ==============================================================================

// Función principal de cálculo de Factores Ambientales (mantiene la lógica de impacto para la columna ImEf)
function calculateImpactEf(index, selectedValue) {
    const multiplier = environmentFactorsWeights[index - 1];
    const impact = selectedValue * multiplier;
    
    // Se guarda el impacto (Peso * Evaluación)
    document.getElementById(`ImEf${index}`).textContent = impact.toFixed(2);
    // CAMBIO AQUÍ: Guardamos con 3 decimales para mantener precisión en el FA total
    localStorage.setItem(`ImpactEf${index}`, impact.toFixed(3));
    localStorage.setItem(`EvaEf${index}`, selectedValue);
    
    // Se calcula el Total (que ahora es el Impacto Ponderado Y el Conteo)
    updateTotalImpactEf();
}

/**
 * Función para calcular y almacenar tanto el TOTAL de Impacto EF (Suma Ponderada)
 * como el TOTAL de Conteo EF (para determinar el CF).
 */
function updateTotalImpactEf() {
    let totalImpactEF = 0; // Suma Ponderada (para la fórmula de FA)
    let totalCountEF = 0;  // Conteo de Reglas (para determinar el CF)
    
    for (let i = 1; i <= environmentFactorsWeights.length; i++) {
        const evaluationValue = parseFloat(localStorage.getItem(`EvaEf${i}`)) || 0;
        // Leemos con 3 decimales para la operación
        const impactValue = parseFloat(localStorage.getItem(`ImpactEf${i}`)) || 0;
        
        // 1. Cálculo del Impacto Ponderado (Total Impacto EF)
        totalImpactEF += impactValue; 

        // 2. Cálculo del Conteo (Total Conteo EF)
        // Solo cuenta si la evaluación es diferente de cero.
        if (evaluationValue !== 0) { 
            if (i >= 1 && i <= 6) {
                // Regla E1 a E6: cuenta si la evaluación es < 3
                if (evaluationValue < 3) {
                    totalCountEF += 1;
                }
            } else if (i >= 7 && i <= 8) {
                // Regla E7 a E8: cuenta si la evaluación es > 3
                if (evaluationValue > 3) {
                    totalCountEF += 1;
                }
            }
        }
    }

    // El elemento "totalEf" ahora muestra la SUMA PONDERADA (que es el valor que entra a la fórmula de FA)
    document.getElementById("totalEf").textContent = totalImpactEF.toFixed(2); // Mostramos a 2 decimales 
    localStorage.setItem("totalImpactEfValue", totalImpactEF.toFixed(3)); // Guardamos a 3 decimales para la operación FA
    
    // El Conteo se guarda por separado solo para la función de CF
    localStorage.setItem("totalCountEfValue", totalCountEF.toFixed(0));


    // El cálculo del FA usa el Impacto Ponderado (totalImpactEF)
    calcularEF(totalImpactEF);
}

// Función para calcular el FA: FA = 1.4 + (-0.03 * Ef)
function calcularEF(totalImpact = null) {
    if (totalImpact === null) {
        // Si se llama sin argumento, usa el valor del impacto ponderado guardado (3 decimales)
        totalImpact = parseFloat(localStorage.getItem("totalImpactEfValue")) || 0; 
    }
    const fa = 1.4 + (-0.03 * totalImpact);
    
    document.getElementById("totalEF").textContent = fa.toFixed(2); // CAMBIO AQUÍ: Mostramos a 2 decimales
    localStorage.setItem("faValue", fa.toFixed(3)); // Guardamos a 3 decimales para la operación UCP
    
    // Al cambiar FA, se recalculan el UCP y el Esfuerzo
    calcularUCP(); 
}

// Inicializa los selects en la tabla de Factores Ambientales (E)
function loadTableData4() {
    // CAMBIO AQUÍ: Leemos el valor guardado (3 decimales) y lo mostramos a 2
    const faValue = parseFloat(localStorage.getItem("faValue")) || 0;
    document.getElementById("totalEF").textContent = faValue.toFixed(2);

    for (let i = 1; i <= environmentFactorsWeights.length; i++) {
        const evaluationCell = document.getElementById(`EvaEf${i}`);
        
        // Crear un select para las evaluaciones
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

        // Cargar valor guardado
        const savedValue = localStorage.getItem(`EvaEf${i}`);
        if (savedValue) {
            select.value = savedValue;
            // Carga el impacto previamente guardado (aún si no se usa para el total) y lo muestra a 2 decimales
            document.getElementById(`ImEf${i}`).textContent = parseFloat(localStorage.getItem(`ImpactEf${i}`) || 0).toFixed(2);
        }

        // Evento para calcular el impacto al cambiar el valor
        select.addEventListener('change', function() {
            const selectedValue = parseInt(this.value);
            if (!isNaN(selectedValue)) {
                calculateImpactEf(i, selectedValue);
            } else {
                document.getElementById(`ImEf${i}`).textContent = '0.00';
                localStorage.removeItem(`EvaEf${i}`);
                localStorage.setItem(`ImpactEf${i}`, '0.000'); // Guardar con 3 decimales
                updateTotalImpactEf(); // Vuelve a calcular el total (Impacto Ponderado y Conteo)
            }
        });

        evaluationCell.appendChild(select);
    }
}


// ==============================================================================
// 5. CÁLCULO DE UCP AJUSTADO Y ESFUERZO (E)
// ==============================================================================

// Función para calcular el UCP ajustado: UCP = UUCP * TCF * FA
function calcularUCP() {
    const UUCP = parseFloat(document.getElementById("uucp").textContent) || 0;
    // Leemos los valores guardados a 3 decimales para la operación
    const TCF = parseFloat(localStorage.getItem("tcfValue")) || 0;
    const FA = parseFloat(localStorage.getItem("faValue")) || 0;
    
    const UCP = UUCP * TCF * FA;
    
    document.getElementById("ttuucp").textContent = UUCP.toFixed(0);
    // Mostramos TCF y FA a 2 decimales
    document.getElementById("tttcf").textContent = TCF.toFixed(2); // CAMBIO AQUÍ: Mostramos a 2 decimales
    document.getElementById("ttef").textContent = FA.toFixed(2); // CAMBIO AQUÍ: Mostramos a 2 decimales
    document.getElementById("ttucp").textContent = UCP.toFixed(2); // CAMBIO AQUÍ: Mostramos a 2 decimales
    
    localStorage.setItem("ucpValue", UCP.toFixed(3)); // Guardamos a 3 decimales para la operación de Esfuerzo

    calcularEsfuerzo(); // Vuelve a calcular el Esfuerzo ya que el UCP cambió
}

/**
 * Determina el Factor de Conversión (CF) automáticamente basado en el Conteo de Factores Ambientales.
 * @returns {number} El Factor de Conversión (CF) (20, 28, o 36).
 */
function calcularCFAutomatica() {
    // Leer el Total de Factores Ambientales que es el CONTEO, guardado por separado.
    const totalConteo = parseFloat(localStorage.getItem("totalCountEfValue")) || 0;
    
    let CF = 0;

    // Lógica de los rangos basada en el CONTEO
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

// Función para calcular el Esfuerzo (E): E = CF * UCP
function calcularEsfuerzo() {
    
    // 1. Obtener CF automáticamente
    const cfValue = calcularCFAutomatica();
    
    // 2. Obtener UCP (valor guardado a 3 decimales)
    const ucpValue = parseFloat(localStorage.getItem("ucpValue")) || 0;
    
    // 3. Calcular Esfuerzo
    const esfuerzoE = cfValue * ucpValue;

    // 4. Actualizar celdas
    document.getElementById("ttCF").textContent = cfValue.toFixed(0); // Muestra el CF calculado
    document.getElementById("tttUCP").textContent = ucpValue.toFixed(2); // CAMBIO AQUÍ: Mostramos UCP a 2 decimales
    document.getElementById("ttE").textContent = esfuerzoE.toFixed(2); // CAMBIO AQUÍ: Mostramos Esfuerzo a 2 decimales

    localStorage.setItem("esfuerzoE", esfuerzoE.toFixed(3)); // Guardamos Esfuerzo a 3 decimales para cálculos posteriores

    // Calcular totales de tiempo
    calcularTotalesEsfuerzo(esfuerzoE);
    
    // Actualizar la tabla de Horas/Persona si ya está cargada
    const ehCell = document.getElementById("eh");
    if (ehCell) {
        ehCell.textContent = esfuerzoE.toFixed(2); // CAMBIO AQUÍ: Mostramos Esfuerzo a 2 decimales
        calcularTotalHorasPersona();
    }
}

// Función para calcular totales de esfuerzo (Horas, Semanas, Meses)
function calcularTotalesEsfuerzo(esfuerzoE) {
    const totalHoras = esfuerzoE;
    // Asumiendo 40 horas laborables por semana
    const totalSemanas = totalHoras / 40; 
    // Asumiendo 4.333 semanas por mes
    const totalMeses = totalSemanas / 4.333;

    document.getElementById("tth").textContent = totalHoras.toFixed(2); // CAMBIO AQUÍ: Mostramos a 2 decimales
    document.getElementById("tts").textContent = totalSemanas.toFixed(2);
    document.getElementById("ttm").textContent = totalMeses.toFixed(2);

    localStorage.setItem("totalHoras", totalHoras.toFixed(3)); // Guardamos a 3 decimales
}

// Inicializa la tabla de Horas/Persona
function loadHorasPersonaTable() {
    const emCell = document.getElementById("em");
    
    // Crear un input numérico para Empleados Asignados
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

        emCell.innerHTML = ''; // Limpiar la celda de HTML estático
        emCell.appendChild(emInput);
    }
    
    // Cargar esfuerzo total (E) en la celda 'eh' y mostrarlo a 2 decimales
    document.getElementById("eh").textContent = parseFloat(localStorage.getItem("esfuerzoE") || 0).toFixed(2); // CAMBIO AQUÍ: Mostramos a 2 decimales
    
    // Cargar total de Horas/Persona si existe
    document.getElementById("temh").textContent = parseFloat(localStorage.getItem("totalHP") || 0).toFixed(2); // CAMBIO AQUÍ: Mostramos a 2 decimales

    calcularTotalHorasPersona();
}

// Función para calcular el total de horas por persona: HP = E / Empleados
function calcularTotalHorasPersona() {
    // Usamos el valor de Esfuerzo guardado a 3 decimales para la operación
    const ehValue = parseFloat(localStorage.getItem("esfuerzoE")) || 0;
    const emInput = document.getElementById("inputEm");
    
    // Usar 1 por defecto si el input está vacío o es inválido para evitar NaN o división por cero
    const emValue = parseFloat(emInput ? emInput.value : 1) || 1; 

    const totalHP = ehValue / emValue;

    document.getElementById("temh").textContent = totalHP.toFixed(2); // CAMBIO AQUÍ: Mostramos a 2 decimales
    localStorage.setItem("totalHP", totalHP.toFixed(3)); // Guardamos a 3 decimales
}