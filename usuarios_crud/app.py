import os

from flask import Flask, abort, redirect, render_template, request, url_for

from mysqlconnection import connectToMySQL

app = Flask(__name__)
BASE_DE_DATOS = "mydb"


def consultar(query, datos=None):
    try:
        return connectToMySQL(BASE_DE_DATOS).query_db(query, datos)
    except Exception:
        return False


def obtener_usuario(usuario_id):
    usuarios = consultar(
        "SELECT id, nombre, apellido, email, created_at, updated_at "
        "FROM usuarios WHERE id = %s",
        (usuario_id,),
    )

    if usuarios is False:
        return False
    if not usuarios:
        return None
    return usuarios[0]


@app.route("/")
def inicio():
    return redirect(url_for("listar_usuarios"))


@app.route("/usuarios")
def listar_usuarios():
    usuarios = consultar(
        "SELECT id, nombre, apellido, email, created_at "
        "FROM usuarios ORDER BY id DESC"
    )

    if usuarios is False:
        return render_template("usuarios.html", usuarios=[]), 503

    return render_template("usuarios.html", usuarios=usuarios)


@app.route("/usuarios/nuevo")
def nuevo_usuario():
    return render_template("nuevo_usuario.html")


@app.route("/usuarios/crear", methods=["POST"])
def crear_usuario():
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    email = request.form.get("email", "").strip()
    datos = {
        "nombre": nombre,
        "apellido": apellido,
        "email": email,
    }

    if not nombre or not apellido or not email:
        return render_template("nuevo_usuario.html", datos=datos), 400

    if any(len(valor) > 45 for valor in datos.values()):
        return render_template("nuevo_usuario.html", datos=datos), 400

    correo_existente = consultar(
        "SELECT id FROM usuarios WHERE email = %s LIMIT 1",
        (email,),
    )

    if correo_existente is False:
        return render_template("nuevo_usuario.html", datos=datos), 503

    if correo_existente:
        return render_template("nuevo_usuario.html", datos=datos), 409

    usuario_guardado = consultar(
        "INSERT INTO usuarios (nombre, apellido, email, created_at, updated_at) "
        "VALUES (%s, %s, %s, NOW(), NOW())",
        (nombre, apellido, email),
    )

    if usuario_guardado is False:
        return render_template("nuevo_usuario.html", datos=datos), 503

    return redirect(url_for("listar_usuarios"))


@app.route("/usuarios/<int:usuario_id>")
def ver_usuario(usuario_id):
    usuario = obtener_usuario(usuario_id)

    if usuario is False:
        return "", 503
    if usuario is None:
        abort(404)

    return render_template("ver_usuario.html", usuario=usuario)


@app.route("/usuarios/editar/<int:usuario_id>", methods=["GET", "POST"])
def editar_usuario(usuario_id):
    usuario = obtener_usuario(usuario_id)

    if usuario is False:
        return "", 503
    if usuario is None:
        abort(404)

    if request.method == "POST":
        datos = {
            "id": usuario_id,
            "nombre": request.form.get("nombre", "").strip(),
            "apellido": request.form.get("apellido", "").strip(),
            "email": request.form.get("email", "").strip(),
        }

        if not datos["nombre"] or not datos["apellido"] or not datos["email"]:
            return render_template("editar_usuario.html", usuario=datos), 400

        if any(len(valor) > 45 for valor in datos.values() if isinstance(valor, str)):
            return render_template("editar_usuario.html", usuario=datos), 400

        correo_existente = consultar(
            "SELECT id FROM usuarios WHERE email = %s AND id <> %s LIMIT 1",
            (datos["email"], usuario_id),
        )

        if correo_existente is False:
            return "", 503
        if correo_existente:
            return render_template("editar_usuario.html", usuario=datos), 409

        actualizado = consultar(
            "UPDATE usuarios SET nombre = %s, apellido = %s, email = %s, "
            "updated_at = NOW() WHERE id = %s",
            (datos["nombre"], datos["apellido"], datos["email"], usuario_id),
        )

        if actualizado is False:
            return "", 503

        return redirect(url_for("listar_usuarios"))

    return render_template("editar_usuario.html", usuario=usuario)


@app.route("/usuarios/borrar/<int:usuario_id>")
def borrar_usuario(usuario_id):
    usuario = obtener_usuario(usuario_id)

    if usuario is False:
        return "", 503
    if usuario is None:
        return redirect(url_for("listar_usuarios"))

    eliminado = consultar(
        "DELETE FROM usuarios WHERE id = %s",
        (usuario_id,),
    )

    if eliminado is False:
        return "", 503

    return redirect(url_for("listar_usuarios"))


if __name__ == "__main__":
    modo_debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=modo_debug)
