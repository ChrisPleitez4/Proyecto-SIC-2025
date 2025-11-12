document.addEventListener("DOMContentLoaded", () => {
    // --- Variables de estado ---
    const puestos = []; // [{id, nombre, salarioHora, cantidad, costoTotal}]
    const cifs = [];    // [{descripcion, monto}] - CIFs manuales

    // --- Elementos DOM ---
    const horasInput = document.getElementById("horas_persona");
    const tablaPuestosBody = document.querySelector("#tablaPuestos tbody");
    const tablaCifBody = document.querySelector("#tablaCif tbody");
    const modalPuestoEl = document.getElementById("modalPuesto");
    const modalCifEl = document.getElementById("modalCif");

    let messageTimeout;
    const toMoney = num => parseFloat(num || 0).toFixed(2);

    // --- Utilidades ---

    // Prefill desde UCP (localStorage.totalHP)
    (function prefillHorasDesdeUCP(){
        const hp = parseFloat(localStorage.getItem("totalHP"));
        if (Number.isFinite(hp) && hp > 0) {
            horasInput.value = hp.toFixed(2);
        }
    })();

    // Notificación de feedback simple
    const showFeedback = (type, message, duration = 5000) => {
        const container = document.getElementById("feedback-message");
        
        if (messageTimeout) clearTimeout(messageTimeout);
        
        container.className = 'mt-3';
        container.innerHTML = '';
        
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const color = type === 'success' ? '#198754' : '#dc3545';

        container.classList.add('alert', alertClass, 'p-2', 'fade', 'show');
        container.innerHTML = `<span style="color: ${color};"></span> ${message}`;
        
        messageTimeout = setTimeout(() => {
            container.classList.remove('show');
            container.innerHTML = '';
        }, duration);
    };
    
    // Obtener token CSRF
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

    // --- Lógica Principal de Cálculo ---

    const actualizarCalculos = () => {
        // Limpiar cualquier feedback anterior al recálculo
        if (messageTimeout) clearTimeout(messageTimeout);
        document.getElementById("feedback-message").innerHTML = '';
        document.getElementById("feedback-message").className = 'mt-3';


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
            // Actualizar resumen
            document.getElementById("tasa_cif_pro").innerText = toMoney(data.tasa_cif);
            document.getElementById("total_cif").innerText    = toMoney(data.total_cif_proyecto); 
            document.getElementById("variacion").innerText    = toMoney(data.variacion);
            document.getElementById("utilidad").innerText     = toMoney(data.utilidad);
            document.getElementById("costo_produccion").innerText = toMoney(data.costo_produccion);
            document.getElementById("precio_venta").innerText     = toMoney(data.precio_venta);
            document.getElementById("anticipo").innerText     = toMoney(data.anticipo); 
            document.getElementById("iva").innerText          = toMoney(data.iva);
            document.getElementById("anticipo_total").innerText = toMoney(data.anticipo_total);
            document.getElementById("diferencia_pendiente").innerText = toMoney(data.diferencia);
            
            // Actualizar tabla CIF (incluye admin, fijos y manuales)
            actualizarTablaCifs(data.cifs_aplicados);
        })
        .catch(error => console.error('Error al calcular:', error));
    };

    const actualizarTablaCifs = (cifsAplicados) => {
        tablaCifBody.innerHTML = ''; 
        if (cifsAplicados && cifsAplicados.length > 0) {
             cifsAplicados.forEach(cif => {
                 const fila = `
                     <tr>
                         <td>${cif.descripcion}</td>
                         <td>$${toMoney(cif.monto)}</td>
                     </tr>`;
                 tablaCifBody.insertAdjacentHTML("beforeend", fila);
             });
        }
    }

    // --- Listeners de Eventos ---

    // Listener para actualizar horas o UCP
    window.addEventListener("storage", (e) => {
        if (e.key === "totalHP") {
            const v = parseFloat(e.newValue);
            if (Number.isFinite(v) && v > 0) {
                horasInput.value = v.toFixed(2);
                actualizarCalculos();
            }
        }
    });

    horasInput.addEventListener("input", actualizarCalculos);

    // Modal Puesto: Cargar salario
    document.getElementById("puestoSelect").addEventListener("change", e => {
        const option = e.target.selectedOptions[0];
        const salario = option.getAttribute("data-salario");
        document.getElementById("salarioHora").value = salario && !isNaN(salario) ? parseFloat(salario).toFixed(2) : "";
    });

    // Modal Puesto: Agregar
    document.getElementById("btnAgregarPuesto").addEventListener("click", () => {
        const select = document.getElementById("puestoSelect");
        const option = select.selectedOptions[0];
        const id = select.value;
        const nombre = option.text;
        const salarioHora = parseFloat(document.getElementById("salarioHora").value);
        const cantidad = parseInt(document.getElementById("cantidadPersonas").value);

        if (!id || isNaN(salarioHora) || isNaN(cantidad) || cantidad <= 0) {
            showFeedback('error', 'Complete correctamente todos los campos del puesto.');
            return;
        }

        const horas = parseFloat(horasInput.value) || 0;
        const costoTotal = salarioHora * cantidad * horas;

        puestos.push({ id, nombre, salarioHora, cantidad, costoTotal });

        // Actualizar visualmente la tabla MOD
        const fila = `
            <tr>
                <td>${nombre}</td>
                <td>${cantidad}</td>
                <td>$${toMoney(salarioHora)}</td>
                <td>$${toMoney(costoTotal)}</td>
            </tr>`;
        tablaPuestosBody.insertAdjacentHTML("beforeend", fila);

        // Limpiar inputs y cerrar modal
        select.value = "";
        document.getElementById("salarioHora").value = "";
        document.getElementById("cantidadPersonas").value = "";
        bootstrap.Modal.getInstance(modalPuestoEl)?.hide();

        actualizarCalculos();
    });

    // Modal CIF: Agregar
    document.getElementById("btnAgregarCif").addEventListener("click", () => {
        const descripcion = document.getElementById("descripcionCif").value.trim();
        const monto = parseFloat(document.getElementById("montoCif").value);

        if (!descripcion || isNaN(monto) || monto <= 0) {
            showFeedback('error', 'Complete correctamente la descripción y el monto del CIF.');
            return;
        }

        const montoDosDecimales = parseFloat(monto.toFixed(2));
        cifs.push({ descripcion, monto: montoDosDecimales });

        // Limpiar inputs y cerrar modal
        document.getElementById("descripcionCif").value = "";
        document.getElementById("montoCif").value = "";
        bootstrap.Modal.getInstance(modalCifEl)?.hide();

        actualizarCalculos();
    });
    
    // Guardar anticipo
    document.getElementById("guardarAnticipo").addEventListener("click", () => {
        const nombreProyecto = document.getElementById("nombre_proyecto").value.trim();
        const anticipo = parseFloat(document.getElementById("anticipo").innerText);
        const iva = parseFloat(document.getElementById("iva").innerText);
        const anticipoTotal = parseFloat(document.getElementById("anticipo_total").innerText);
        const precioVenta = parseFloat(document.getElementById("precio_venta").innerText);
        const diferencia = parseFloat(document.getElementById("diferencia_pendiente").innerText);

        if (!nombreProyecto) {
            showFeedback('error', 'El nombre del proyecto es obligatorio.');
            return;
        }
        
        if (isNaN(anticipo) || anticipo <= 0) {
            showFeedback('error', 'Debe calcular primero el costo antes de guardar el anticipo.', 3000);
            return;
        }

        fetch("/costosventa/guardar_anticipo/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({
                nombre_proyecto: nombreProyecto,
                anticipo: anticipo.toFixed(2),
                iva: iva.toFixed(2),
                anticipo_total: anticipoTotal.toFixed(2),
                precio_venta: precioVenta.toFixed(2),
                diferencia: diferencia.toFixed(2)
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                // Mostrar mensaje de éxito y recargar
                showFeedback('success', data.mensaje + " Recargando...", 1500);
                setTimeout(() => {
                    window.location.reload(); 
                }, 1500);

            } else if (data.status === 'error') {
                // Mostrar mensaje de error
                showFeedback('error', data.error);
            } else {
                 showFeedback('error', 'Respuesta inesperada del servidor.');
            }
        })
        .catch(error => {
            console.error('Error al guardar el anticipo:', error);
            showFeedback('error', 'Ocurrió un error de conexión al intentar guardar.');
        });
    });

    // Cálculo inicial (por si ya venía totalHP)
    actualizarCalculos();
});