class ChatView {
    _onlineListHtml = null;
    _chatWindow = null;
    _buttonScroll = null;
    constructor() {
        this._onlineListHtml = document.getElementById('users-list')
        this._chatWindow = document.getElementById("chat-messages");
        this._buttonScroll = document.getElementById('button_scroll_down')
    }

    removeUserFromOnline(username_leaved) {
        this._onlineListHtml.removeChild(this._onlineUsers.get(username_leaved))
        this._onlineUsers.delete(username_leaved)
    }

    appendMessage(data) {
        let li = document.createElement("li");
        li.appendChild(document.createTextNode(data["username"] + ": " + data["text"]));
        this._chatWindow.appendChild(li);
        this.scrollToBottom(this._chatWindow)
    }

     addUserToOnlineList(username) {
        let li = document.createElement("li");
        li.id = username
        li.appendChild(document.createTextNode(username));
        this._onlineListHtml.appendChild(li);
        this._onlineUsers.set(username, li);
    }

    sendMessage() {
        let message = document.getElementById("message").value;
        this._socket.emit("new_message", JSON.stringify({'text': message}));
        document.getElementById("message").value = "";
    }

    enterKeyListener() {
        document.getElementById("message").addEventListener("keyup", event => {
            if (event.key == "Enter") {
                this.sendMessage()
            }
        })
    }

    clickListener() {
        document.getElementById("send_msg").addEventListener('click', event => {
            console.log('Клик')
            this.sendMessage()
        })
    }

    scrollToBottom(element) {
        element.scrollTop = element.scrollHeight;
    }
}
export {ChatView};