document.addEventListener("DOMContentLoaded", function () {
    const botones = document.querySelectorAll(".btn-detalle");
    const modal = document.getElementById("detalleModal");
    const contenido = document.getElementById("detalleContenido");
    const span = modal.querySelector(".close");

    // Función para abrir modal
    function abrirModal(html) {
        contenido.innerHTML = html;
        modal.style.display = "block";
        document.body.style.overflow = "hidden"; // Bloquear scroll fondo
    }

    // Función para cerrar modal
    function cerrarModal() {
        modal.style.display = "none";
        document.body.style.overflow = ""; // Restaurar scroll
    }

    // Evento para cada botón
    botones.forEach(boton => {
        boton.addEventListener("click", function () {
            const nro = boton.getAttribute("data-nro");
            const periodo = boton.getAttribute("data-periodo");
            const url = `/libromayor/detalle/?nro=${encodeURIComponent(nro)}&periodo=${encodeURIComponent(periodo)}`;

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        abrirModal(`<p>${data.error}</p>`);
                        return;
                    }

                    let totalDebe = 0;
                    let totalHaber = 0;
                    let html = `
                        <h3>Transacción #${data.codigo}</h3>
                        <p><strong>Fecha:</strong> ${data.fecha}</p>
                        <p><strong>Descripción:</strong> ${data.descripcion}</p>
                        <hr>
                        <h4>Movimientos:</h4>
                        <table class="table table-striped table-bordered tabla-detalle">
                            <thead>
                                <tr>
                                    <th>Cuenta</th>
                                    <th>Debe ($)</th>
                                    <th>Haber ($)</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    data.movimientos.forEach(mov => {
                        // Conversión segura a número
                        const debe = Number(mov.debe || 0);
                        const haber = Number(mov.haber || 0);

                        totalDebe += debe;
                        totalHaber += haber;

                        html += `
                            <tr>
                                <td>${mov.cuenta}</td>
                                <td>${debe.toFixed(2)}</td>
                                <td>${haber.toFixed(2)}</td>
                            </tr>
                        `;
                    });

                    html += `
                            </tbody>
                            <tfoot>
                                <tr class="fw-bold">
                                    <td>Total</td>
                                    <td>${totalDebe.toFixed(2)}</td>
                                    <td>${totalHaber.toFixed(2)}</td>
                                </tr>
                            </tfoot>
                        </table>
                    `;

                    abrirModal(html);
                })
                .catch(err => {
                    abrirModal(`<p>Error al cargar la transacción: ${err}</p>`);
                });
        });
    });

    // Eventos de cierre del modal
    span.addEventListener("click", cerrarModal);
    window.addEventListener("click", function (event) {
        if (event.target === modal) cerrarModal();
    });
    window.addEventListener("keydown", function (e) {
        if (e.key === "Escape") cerrarModal();
    });
});