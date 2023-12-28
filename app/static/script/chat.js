import { ChatView } from './chatView.js';

// Now you can use the ChatView class
const chatViewInstance = new ChatView();

class User {
    username = null;
    constructor(username) {
        this.username = username
    }

    toJson() {
        return JSON.stringify({"username": this.username})
    }

    fromJson(string) {
        let jsonObject = JSON.parse(string)
        return new User(jsonObject['username'])
    }
}

class Message {
    _senderUsername = null;
    _text = null;
    _date = null
    constructor(senderUsername, text, date) {
        this._senderUsername = senderUsername;
        this._text = text;
        this._date = date;
    }

    toJson() {
        return JSON.stringify({"username": this._senderUsername, 'text': this._text, 'date': this._date})
    }

    fromJson(string) {
        let jsonObject = JSON.parse(string)
        return new Message(jsonObject['username'], jsonObject['text'], jsonObject['date'])
    }
}

class JoinMessage extends Message {
    constructor(username, date) {
        super(username, null, date);
    }

    toJson() {
        return JSON.stringify({'username': this._senderUsername, 'date': this._date})
    }

    fromJson(string) {
        let jsonObject = JSON.parse(string)
        return new JoinMessage(jsonObject['username'], jsonObject['date'])
    }
}

class ChatController {
    _socket = null;
    _onlineListHtml = null;
    _onlineUsers = null;
    _currentUser = null;
    notificationSound = new Audio("/static/sound/msg_notify.mp3");
    _chatWindow = null;
    constructor() {
        this._socket = io({autoConnect: false});
        this._onlineListHtml = document.getElementById('users-list')
        this._onlineUsers = new Map()
        this.getCurrentUser().then(username => this._currentUser = username)
        this._chatWindow = document.getElementById("chat-messages");
        this._buttonScroll = document.getElementById('button_scroll_down')
        this._socket.connect()
        this.subscribeOnEvent()
        this.getHistory()
        this.getOnlineUsers()
        this.enterKeyListener()
        this.clickListener()
        this._chatWindow.addEventListener('scroll', (event) => {
            if (!(this._chatWindow.scrollHeight - this._chatWindow.scrollTop <= this._chatWindow.clientHeight)) {
                this._buttonScroll.style.display = 'block'
                return;
            }
            this._buttonScroll.style.display = 'none'
        })
        this._buttonScroll.addEventListener('click', event => {

            this.scrollToBottom(this._chatWindow)
        })

    }

    subscribeOnEvent() {
        this._socket.on("connect", () => {
        })
        this._socket.on('disconnect', (reason) => {
            if (reason === "io server disconnect") {
                // the disconnection was initiated by the server, you need to reconnect manually
                this._socket.connect();
            }
        })
        this._socket.on("chat", data => {
            if(data['username'] !== this._currentUser.username)
                this.notificationSound.play();
            this.appendMessage(data)
        })
        this._socket.on('leave', data => {
            // Если пришло увдомление о выходи, удаляем из списка html и списка
            console.log('leaved')
            this.removeUserFromOnline(data['username'])
        })
        this._socket.on('join', data => {
            console.log(data)
            this.addUserToOnlineList(data['username'])
        })
    }

    removeUserFromOnline(username_leaved) {
        if(!this._onlineUsers.get(username_leaved))
            return
        this._onlineListHtml.removeChild(this._onlineUsers.get(username_leaved))
        this._onlineUsers.delete(username_leaved)
    }

    onUserJoin() {

    }

    onUserLeaved(leavedUser) {

    }

    convetDate(date) {
        let serverDate = new Date(date);
        let timezoneOffset = serverDate.getTimezoneOffset();
        let clientTime = new Date(serverDate.getTime() - (timezoneOffset * 60 * 1000));
        return clientTime.toLocaleString('ru-RU', {
            year: 'numeric',
            month: 'numeric',
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric',
            hour12: false
        });

    }

    appendMessage(data) {
        if(!data['text'])
            return
        let li = document.createElement("li");
        let username_element = document.createElement('strong')
        username_element.appendChild(document.createTextNode(data["username"]))
        li.appendChild(username_element);
        if(!data['date'])
            data['date'] = new Date().toDateString()
        li.appendChild(document.createTextNode(` ${this.convetDate(data['date'])}`))
        li.appendChild(document.createElement('br'));
        li.appendChild(document.createTextNode(data["text"]))

        this._chatWindow.appendChild(li);
        this.scrollToBottom(this._chatWindow)
    }

    getOnlineUsers() {
        fetch('get-online').then(response => {
            if(!response.ok)
                throw new Error('Server is response faield')
            return response.json()
        }).then(data => {
            console.log(this._onlineUsers)
            data.forEach(user => {
                if(this.isCurrentUser(user))
                    return;

                for (let onlineUsersKey in this._onlineUsers.keys()) {
                    console.log(onlineUsersKey)
                }
                this.addUserToOnlineList(user)
            })
        }).catch(error => {
            throw new Error(`User is invalid ${error}`)
        })

    }

    isCurrentUser(username) {
        return this._currentUser === username
    }

    addUserToOnlineList(username) {
        let li = document.createElement("li");
        li.id = username
        if(username == this._currentUser.username)
            li.appendChild(document.createTextNode('(Вы) ' + username))
        else
            li.appendChild(document.createTextNode(username));
        this._onlineListHtml.appendChild(li);
        this._onlineUsers.set(username, li);
    }

    getCurrentUser() {
        return fetch('get-username').then(response => {
            if(!response.ok)
                throw new Error('Server is response faield')
            return response.json()
        }).then(data => {
            return new User(data.username)
        }).catch(error => {
            throw new Error(`User is invalid ${error}`)
        })

    }

    getHistory() {
        fetch('get-history').then(response => {
            return response.json()
        }).then(data => {
            data.messages.forEach(msg => {
                this.appendMessage(msg)
            })
            this.scrollToBottom(this._chatWindow)
        })
        let ul = document.getElementById("chat-messages");
    }

    sendMessage() {
        let text = document.getElementById("message").value;
        let message = new Message(this._currentUser, text, Math.floor(new Date().getTime() / 1000))
        this._socket.emit("new_message", message.toJson());
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

new ChatController()
