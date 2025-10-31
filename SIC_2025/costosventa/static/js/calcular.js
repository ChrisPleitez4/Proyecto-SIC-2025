document.addEventListener("DOMContentLoaded", () => {
    const puestos = [];
    const cifs = [];

    const horasInput = document.getElementById("horas_persona");

    const toMoney = num => parseFloat(num || 0).toFixed(2);

    const actualizarCalculos = () => {
        fetch("/costosventa/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({
                horas_persona: horasInput.value,
                puestos: JSON.stringify(puestos),
                cifs: JSON.stringify(cifs)
            })
        })
        .then(res => res.json())
        .then(data => {
            document.getElementById("tasa_cif_pro").innerText = toMoney(data.tasa_cif);
            document.getElementById("total_cif").innerText = toMoney(data.total_cif_proyecto);
            document.getElementById("variacion").innerText = toMoney(data.variacion);
            document.getElementById("utilidad").innerText = toMoney(data.utilidad);
            document.getElementById("costo_produccion").innerText = toMoney(data.costo_produccion);
            document.getElementById("costo_venta").innerText = toMoney(data.costo_venta);
            document.getElementById("anticipo").innerText = toMoney(data.anticipo);
        });
    };

    // Modal puesto
    document.getElementById("puestoSelect").addEventListener("change", e => {
        const option = e.target.selectedOptions[0];
        const salario = option.getAttribute("data-salario");
        document.getElementById("salarioHora").value = salario && !isNaN(salario) ? parseFloat(salario).toFixed(2) : "";
    });

    document.getElementById("btnAgregarPuesto").addEventListener("click", () => {
        const select = document.getElementById("puestoSelect");
        const option = select.selectedOptions[0];
        const id = select.value;
        const nombre = option.text;
        const salarioHora = parseFloat(document.getElementById("salarioHora").value);
        const cantidad = parseInt(document.getElementById("cantidadPersonas").value);

        console.log({
            id,
            salarioHora,
            cantidad,
            salarioHoraRaw: document.getElementById("salarioHora").value,
            cantidadRaw: document.getElementById("cantidadPersonas").value
        });


        if (!id || isNaN(salarioHora) || isNaN(cantidad) || cantidad <= 0) {
            alert("Complete correctamente todos los campos del puesto.");
            return;
        }

        const horas = parseFloat(horasInput.value) || 0;
        const costoTotal = salarioHora * cantidad * horas;

        puestos.push({ id, nombre, salarioHora, cantidad, costoTotal });

        const fila = `
            <tr>
                <td>${nombre}</td>
                <td>${cantidad}</td>
                <td>$${toMoney(salarioHora)}</td>
                <td>$${toMoney(costoTotal)}</td>
            </tr>`;
        document.querySelector("#tablaPuestos tbody").insertAdjacentHTML("beforeend", fila);

        // Limpiar modal
        select.value = "";
        document.getElementById("salarioHora").value = "";
        document.getElementById("cantidadPersonas").value = "";
        bootstrap.Modal.getInstance(document.getElementById("modalPuesto")).hide();

        actualizarCalculos();
    });

    // Modal CIF
    document.getElementById("btnAgregarCif").addEventListener("click", () => {
        const descripcion = document.getElementById("descripcionCif").value.trim();
        const monto = parseFloat(document.getElementById("montoCif").value);

        if (!descripcion || isNaN(monto) || monto <= 0) {
            alert("Complete correctamente la descripción y el monto del CIF.");
            return;
        }

        const montoDosDecimales = parseFloat(monto.toFixed(2));
        cifs.push({ descripcion, monto: montoDosDecimales });

        const fila = `
            <tr>
                <td>${descripcion}</td>
                <td>$${toMoney(montoDosDecimales)}</td>
            </tr>`;
        document.querySelector("#tablaCif tbody").insertAdjacentHTML("beforeend", fila);

        // Limpiar modal
        document.getElementById("descripcionCif").value = "";
        document.getElementById("montoCif").value = "";
        bootstrap.Modal.getInstance(document.getElementById("modalCif")).hide();

        actualizarCalculos();
    });

    horasInput.addEventListener("input", actualizarCalculos);

    // Guardar anticipo
    document.getElementById("guardarAnticipo").addEventListener("click", () => {
        const anticipo = parseFloat(document.getElementById("anticipo").innerText);
        const costoVenta = parseFloat(document.getElementById("costo_venta").innerText);

        if (isNaN(anticipo) || anticipo <= 0) {
            alert("Debe calcular primero el costo antes de guardar el anticipo.");
            return;
        }

        fetch("/costosventa/guardar_anticipo/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({
                anticipo: anticipo.toFixed(2),
                costo_venta: costoVenta.toFixed(2)
            })
        })
        .then(res => res.json())
        .then(data => alert(data.mensaje || data.error));
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
