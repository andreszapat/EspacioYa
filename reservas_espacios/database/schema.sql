PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS espacios (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre         TEXT    NOT NULL UNIQUE CHECK (length(trim(nombre)) > 0),
    capacidad      INTEGER NOT NULL CHECK (capacidad > 0),
    ubicacion      TEXT    NOT NULL CHECK (length(trim(ubicacion)) > 0),
    equipamiento   TEXT    NOT NULL DEFAULT '',
    habilitado     INTEGER NOT NULL DEFAULT 1 CHECK (habilitado IN (0, 1)),
    hora_apertura  TEXT    NOT NULL DEFAULT '07:00' CHECK (hora_apertura GLOB '[0-2][0-9]:[0-5][0-9]'),
    hora_cierre    TEXT    NOT NULL DEFAULT '21:00' CHECK (hora_cierre GLOB '[0-2][0-9]:[0-5][0-9]'),
    CHECK (hora_apertura < hora_cierre)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
    correo    TEXT NOT NULL UNIQUE CHECK (correo LIKE '%_@_%._%'),
    rol       TEXT NOT NULL CHECK (rol IN ('estudiante', 'docente', 'administrativo')),
    telefono  TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS reservas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id   INTEGER NOT NULL REFERENCES usuarios (id) ON DELETE RESTRICT,
    espacio_id   INTEGER NOT NULL REFERENCES espacios (id) ON DELETE RESTRICT,
    fecha        TEXT    NOT NULL CHECK (fecha GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'),
    hora_inicio  TEXT    NOT NULL CHECK (hora_inicio GLOB '[0-2][0-9]:[0-5][0-9]'),
    hora_fin     TEXT    NOT NULL CHECK (hora_fin GLOB '[0-2][0-9]:[0-5][0-9]'),
    proposito    TEXT    NOT NULL CHECK (length(trim(proposito)) > 0),
    creada_en    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK (hora_inicio < hora_fin)
);

CREATE INDEX IF NOT EXISTS idx_reservas_espacio_fecha ON reservas (espacio_id, fecha);
CREATE INDEX IF NOT EXISTS idx_reservas_usuario ON reservas (usuario_id);

CREATE TRIGGER IF NOT EXISTS trg_reservas_sin_solape_insert
BEFORE INSERT ON reservas
WHEN EXISTS (
    SELECT 1 FROM reservas r
    WHERE r.espacio_id = NEW.espacio_id
      AND r.fecha = NEW.fecha
      AND r.hora_inicio < NEW.hora_fin
      AND NEW.hora_inicio < r.hora_fin
)
BEGIN
    SELECT RAISE(ABORT, 'CONFLICTO_HORARIO');
END;

CREATE TRIGGER IF NOT EXISTS trg_reservas_sin_solape_update
BEFORE UPDATE ON reservas
WHEN EXISTS (
    SELECT 1 FROM reservas r
    WHERE r.id <> NEW.id
      AND r.espacio_id = NEW.espacio_id
      AND r.fecha = NEW.fecha
      AND r.hora_inicio < NEW.hora_fin
      AND NEW.hora_inicio < r.hora_fin
)
BEGIN
    SELECT RAISE(ABORT, 'CONFLICTO_HORARIO');
END;

CREATE TRIGGER IF NOT EXISTS trg_reservas_horario_insert
BEFORE INSERT ON reservas
WHEN EXISTS (
    SELECT 1 FROM espacios e
    WHERE e.id = NEW.espacio_id
      AND (NEW.hora_inicio < e.hora_apertura OR NEW.hora_fin > e.hora_cierre OR e.habilitado = 0)
)
BEGIN
    SELECT RAISE(ABORT, 'FUERA_DE_HORARIO');
END;

CREATE TRIGGER IF NOT EXISTS trg_reservas_horario_update
BEFORE UPDATE ON reservas
WHEN EXISTS (
    SELECT 1 FROM espacios e
    WHERE e.id = NEW.espacio_id
      AND (NEW.hora_inicio < e.hora_apertura OR NEW.hora_fin > e.hora_cierre OR e.habilitado = 0)
)
BEGIN
    SELECT RAISE(ABORT, 'FUERA_DE_HORARIO');
END;
