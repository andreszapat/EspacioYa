(() => {
  const MENSAJES = {
    valueMissing: "Este campo es obligatorio.",
    typeMismatch: "El formato no es válido.",
    patternMismatch: "El formato no es válido.",
    rangeUnderflow: "El valor es demasiado bajo.",
    rangeOverflow: "El valor es demasiado alto.",
    tooLong: "El texto es demasiado largo.",
  };

  const mensajeDe = (campo) => {
    if (campo.validity.customError) return campo.validationMessage;
    const clave = Object.keys(MENSAJES).find((k) => campo.validity[k]);
    if (!clave) return "";
    return (clave === "patternMismatch" && campo.dataset.mensaje) || MENSAJES[clave];
  };

  const contenedorDe = (campo) => campo.closest(".campo") || campo.parentElement;

  const pintarError = (campo) => {
    const contenedor = contenedorDe(campo);
    let nota = contenedor.querySelector(`.campo__error[data-para="${campo.name}"]`);
    const mensaje = mensajeDe(campo);
    if (!nota) {
      nota = document.createElement("small");
      nota.className = "campo__error";
      nota.dataset.para = campo.name;
      contenedor.appendChild(nota);
    }
    nota.textContent = mensaje;
    campo.classList.toggle("invalido", Boolean(mensaje));
  };

  const validarOrden = (formulario) => {
    formulario.querySelectorAll("[data-despues-de]").forEach((campo) => {
      const referencia = formulario.elements[campo.dataset.despuesDe];
      const invalido = campo.value && referencia && referencia.value && campo.value <= referencia.value;
      campo.setCustomValidity(invalido ? campo.dataset.mensaje || "Valor fuera de orden." : "");
    });
  };

  document.querySelectorAll("form[data-validar]").forEach((formulario) => {
    const campos = () => [...formulario.elements].filter((el) => el.name && el.willValidate);

    formulario.addEventListener("input", (evento) => {
      validarOrden(formulario);
      if (evento.target.classList.contains("invalido")) pintarError(evento.target);
    });

    formulario.addEventListener("focusout", (evento) => {
      if (evento.target.name && evento.target.willValidate) {
        validarOrden(formulario);
        pintarError(evento.target);
      }
    });

    formulario.addEventListener("submit", (evento) => {
      validarOrden(formulario);
      formulario.dispatchEvent(new CustomEvent("antes-de-validar"));
      const invalidos = campos().filter((campo) => !campo.checkValidity());
      campos().forEach(pintarError);
      if (invalidos.length) {
        evento.preventDefault();
        invalidos[0].focus();
      }
    });
  });
})();
