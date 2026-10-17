(() => {
  const formulario = document.getElementById("form-reserva");
  if (!formulario) return;

  const campos = {
    usuario: formulario.elements.usuario_id,
    espacio: formulario.elements.espacio_id,
    fecha: formulario.elements.fecha,
    inicio: formulario.elements.hora_inicio,
    fin: formulario.elements.hora_fin,
  };
  const aviso = document.getElementById("aviso-disponibilidad");
  const listaOcupacion = document.getElementById("ocupacion-lista");
  const textoHorario = document.getElementById("ocupacion-horario");
  const excluir = formulario.dataset.reservaId;

  let ocupadas = [];
  let espacio = null;
  let consultaActual = 0;

  const aMinutos = (hora) => {
    const [h, m] = hora.split(":").map(Number);
    return h * 60 + m;
  };

  const mostrar = (tipo, texto) => {
    aviso.hidden = !texto;
    aviso.className = `alerta alerta--${tipo} campo--ancho`;
    aviso.textContent = texto || "";
  };

  const pintarOcupacion = () => {
    listaOcupacion.replaceChildren();
    if (!espacio) {
      textoHorario.textContent = "Seleccione un espacio y una fecha.";
      return;
    }
    textoHorario.textContent = `${espacio.nombre}: abierto de ${espacio.hora_apertura} a ${espacio.hora_cierre}.`;
    if (!ocupadas.length) {
      const item = document.createElement("li");
      item.className = "ocupacion__libre";
      item.textContent = "Sin reservas: todo el día está libre.";
      listaOcupacion.appendChild(item);
      return;
    }
    ocupadas.forEach((reserva) => {
      const item = document.createElement("li");
      const hora = document.createElement("strong");
      hora.textContent = `${reserva.hora_inicio}–${reserva.hora_fin}`;
      const detalle = document.createElement("span");
      detalle.textContent = `${reserva.usuario} · ${reserva.proposito}`;
      item.append(hora, detalle);
      listaOcupacion.appendChild(item);
    });
  };

  const errores = () => {
    const inicio = campos.inicio.value;
    const fin = campos.fin.value;
    const lista = [];
    if (!inicio || !fin) return lista;

    if (inicio >= fin) {
      lista.push("La hora de fin debe ser posterior a la hora de inicio.");
      return lista;
    }
    if (campos.fecha.value && new Date(`${campos.fecha.value}T${inicio}`) < new Date()) {
      lista.push("No se puede reservar en una fecha u hora que ya pasó.");
    }
    if (espacio && (inicio < espacio.hora_apertura || fin > espacio.hora_cierre)) {
      lista.push(`Fuera de horario: el espacio solo atiende de ${espacio.hora_apertura} a ${espacio.hora_cierre}.`);
    }
    const opcion = campos.usuario.selectedOptions[0];
    const maximo = parseFloat(opcion?.dataset.maxHoras);
    const duracion = (aMinutos(fin) - aMinutos(inicio)) / 60;
    if (maximo && duracion > maximo) {
      lista.push(`Un ${opcion.dataset.rol.toLowerCase()} puede reservar máximo ${maximo} h (solicitó ${duracion} h).`);
    }
    const choque = ocupadas.find((r) => r.hora_inicio < fin && inicio < r.hora_fin);
    if (choque) {
      lista.push(`Conflicto: ya está reservado de ${choque.hora_inicio} a ${choque.hora_fin} por ${choque.usuario}.`);
    }
    return lista;
  };

  const validar = () => {
    const problemas = errores();
    campos.fin.setCustomValidity(problemas[0] || "");
    if (problemas.length) {
      mostrar("error", problemas.join(" "));
    } else if (espacio && campos.inicio.value && campos.fin.value) {
      mostrar("exito", `✓ ${espacio.nombre} está disponible de ${campos.inicio.value} a ${campos.fin.value}.`);
    } else {
      mostrar("", "");
    }
  };

  const cargarOcupacion = async () => {
    ocupadas = [];
    espacio = null;
    const id = campos.espacio.value;
    const fecha = campos.fecha.value;
    const numero = ++consultaActual;
    if (id && fecha) {
      const parametros = new URLSearchParams({ espacio_id: id, fecha });
      if (excluir) parametros.set("excluir", excluir);
      try {
        const respuesta = await fetch(`${formulario.dataset.api}?${parametros}`);
        if (!respuesta.ok) throw new Error(respuesta.statusText);
        const datos = await respuesta.json();
        if (numero !== consultaActual) return;
        ocupadas = datos.reservas;
        espacio = datos.espacio;
      } catch {
        mostrar("aviso", "No se pudo consultar la disponibilidad; el servidor validará la reserva al guardar.");
      }
    }
    pintarOcupacion();
    validar();
  };

  campos.espacio.addEventListener("change", cargarOcupacion);
  campos.fecha.addEventListener("change", cargarOcupacion);
  [campos.usuario, campos.inicio, campos.fin].forEach((campo) => campo.addEventListener("input", validar));
  formulario.addEventListener("antes-de-validar", validar);
  cargarOcupacion();
})();
