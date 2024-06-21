# O import random foi usado para criar os códigos aleatórios da sala
# from string import ascii_uppercase serve para que os códigos da sala estejam em letra maiúscula
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

rooms = {}
# Esta função vai gerar o código da sala em letras maiusculas
def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code
#Esta primeira rota leva para a pagina inicial, é neste lugar que poderá criar salas ou entrar em alguma existente
#Foi usado o método POST para "postar" dados nesta rota, pois, será "postado" dados ao criar ou entrar numa sala
#Será preciso enviar os dados de volta para esta rota
@app.route("/", methods=["POST", "GET"])
def home():
    # A razão para limpar a sessão é que quando o usuario voltar para a pagina inicial é que ele possa digitar outra sala ou outro nome sem que salve a sessão anterior, assim ele poderá trocar de sessão sem problemas
    session.clear()
    # Com o formulario criado, é preciso criar diferentes para cada botão clicado
    # Quando um botão é clicado, uma solicitação do POST é enviada
    # Objetivo é lidar com a solicitação do POST obtendo os diferentes dados do formulário que estão sendo enviados
    # Para criar uma sala ou entrar, precisa verificar se o método request.method é igual a post
    # Isso foi feito para importar a solicitação, e como o método é o tipo de solicitação (post ou get), se for igual a post precisamos pegar os dados do formulário
    # Por isso que para cada elemento do formulário foi criado uma marcação para diferenciar cada botão
    # Para pegar os dados do formulário é só usar o request.form.get e o tipo de dado
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        # Foram criados mensagens de erros para caso o usuario tenta criar uma sala sem nome e tenta entrar numa sala sem código
        if not name:
            return render_template("home.html", error="Por Favor, crie um nome.", code=code, name=name)

        if join != False and not code:
            return render_template("home.html", error="Por Favor, digite o código.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            # A variavel room é o código da salava e a variavel rooms é uma lista vazia, para entrar na sala precisa colocar o código
            #Após criado o código da sala e o usuario entrado na sala, é criado um dicionario com o numero de membros igual a zero e as mensagens salvas numa lista
            rooms[room] = {"members": 0, "messages": []}
        #Caso o usuario coloque um código que não existe, aparece esta mensagem de erro

        elif code not in rooms:
            return render_template("home.html", error="Esta sala não existe.", code=code, name=name)
        #Session é uma forma semipermanente de armazenar informações sobre um usuario
        #Session tem como definição dados temporários armazenados em um servidor
        session["room"] = room
        session["name"] = name
        # Depois de determinar a sala e o nome, o usuario será redirecionado para a sala de bate papo
        return redirect(url_for("room"))

    return render_template("home.html")

# Esta é a rota da sala de bate papo
@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    #Quando uma pessoa entra na sala, o numero de membros aumenta usando uma atribuição +=1
    #Essa é a mensagem que aparece quando o segundo usuario entra na sala
    join_room(room)
    send({"name": name, "message": "acabou de entrar na sala"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} entrou na sala {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    #Quando uma pessoa sai da sala, o numero de membros dimimui usando uma atribuição -=1
    #Essa é a mensagem que aparece quando o segundo usuario sai da sala

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "saiu da sala"}, to=room)
    print(f"{name} saiu da sala {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)