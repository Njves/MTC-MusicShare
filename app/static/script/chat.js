const socket = io({autoConnect: false});
let username = ''
function create() {
    socket.connect();
    fetch('get-username').then(response => {
        return response.json()
    }).then(data => {
        username = data.username
    })
    socket.on("connect", function() {
        socket.emit("user_join", JSON.stringify({"username": username}));
    })
}

function get_history() {
    fetch('get-history').then(response => {
        return response.json()
    }).then(data => {
        data.messages.forEach(msg => {
            add(msg.username, msg.text)
        })
    })
}

function send() {
    let message = document.getElementById("message").value;
    socket.emit("new_message", JSON.stringify({'username': '{{ current_user.username }}', 'message': message}));
    document.getElementById("message").value = "";
}

function add(username, text) {
    let ul = document.getElementById("chat-messages");
    let li = document.createElement("li");
    li.appendChild(document.createTextNode(username + ": " + text));
    ul.appendChild(li);
    ul.scrolltop = ul.scrollHeight;
}

document.getElementById("message").addEventListener("keyup", function (event) {
    if (event.key == "Enter") {
        let message = document.getElementById("message").value;
        socket.emit("new_message", JSON.stringify({'username': '', 'message': message}));
        document.getElementById("message").value = "";
    }
})

socket.on("chat", function(data) {
    console.log(data)
    let ul = document.getElementById("chat-messages");
    let li = document.createElement("li");
    li.appendChild(document.createTextNode(data["username"] + ": " + data["message"]));
    ul.appendChild(li);
    ul.scrolltop = ul.scrollHeight;
})
get_history()