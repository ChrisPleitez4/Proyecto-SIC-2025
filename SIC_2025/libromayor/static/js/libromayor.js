document.addEventListener("DOMContentLoaded", function () {
  const botones = document.querySelectorAll(".btn-detalle");
  const modal = document.getElementById("detalleModal");
  const contenido = document.getElementById("detalleContenido");
  const span = document.querySelector(".close");

  botones.forEach(boton => {
    boton.addEventListener("click", () => {
      const url = boton.getAttribute("data-url");

      fetch(url)
        .then(response => response.json())
        .then(data => {
          if (data.error) {
            contenido.innerHTML = `<p>${data.error}</p>`;
          } else {
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
              html += `
                <tr>
                  <td>${mov.cuenta}</td>
                  <td>${mov.debe.toFixed(2)}</td>
                  <td>${mov.haber.toFixed(2)}</td>
                </tr>
              `;
            });

            html += `</tbody></table>`;
            contenido.innerHTML = html;
          }

          modal.style.display = "block";
        });
    });
  });

  span.onclick = function () {
    modal.style.display = "none";
  };

  window.onclick = function (event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  };

  window.addEventListener("keydown", function(e) {
    if(e.key === "Escape") modal.style.display = "none";
  });
});