import {ChatView} from './chatView.js';

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
    _roomId = null;
    constructor(senderUsername, text, date, roomId) {
        this._senderUsername = senderUsername;
        this._text = text;
        this._date = date;
        this._roomId = roomId;
    }

    toJson() {
        return JSON.stringify({"username": this._senderUsername, 'text': this._text, 'date': this._date, 'room_id': this._roomId})
    }

    fromJson(string) {
        let jsonObject = JSON.parse(string)
        return new Message(jsonObject['username'], jsonObject['text'], jsonObject['date'], jsonObject['room_id'])
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

class Room {
    _name = null;
    _id = null;
    _members = null;
    constructor(name, id, members) {
        this.name = name;
        this.id = id;
        this.members = members
    }

    toJson() {
        return JSON.stringify({'name': this._name, 'id': this._id, 'members': this._members})
    }

    fromJson(string) {
        let jsonObject = JSON.parse(string)
        return new Room(jsonObject['name'], jsonObject['id'], jsonObject['members'])
    }
}

class ChatController {
    _socket = null;
    _onlineListHtml = null;
    _onlineUsers = null;
    _currentUser = null;
    notificationSound = new Audio("/get-notify-message")
    _chatWindow = null;
    _roomList = null;
    _inputFileAttach = null;
    _attachPreview = null;
    _sendAttach = null;
    _attachForm = null;
    _loader = null;
    _loaderRooms = null;
    _loaderOnline = null;
    _searchForm = null;
    _searchRun = null;
    _roomsModels = null;
    _currentRoom = null;
    _highLightedElement = null;
    _sendCreateRoom = null;
    constructor() {
        this._socket = io({autoConnect: false});
        this._onlineListHtml = document.getElementById('users-list')
        this._onlineUsers = new Map()
        this.getCurrentUser().then(user => {
            this._currentUser = user['username']
            this._currentRoom = user['room']
            console.log(this._currentRoom)
            console.log(this._currentUser)
            this.getOnlineUsers(user['username'])
            this.getHistory()
            this.getRooms().then(rooms => {
                this.highLightCurrentRoom(this._currentRoom)
            })

        })
        this._chatWindow = document.getElementById("chat-messages");
        this._buttonScroll = document.getElementById('button_scroll_down')
        this._socket.connect()
        this._roomsModels = new Map()
        this._roomList = document.getElementById('rooms-list')
        this._inputFileAttach = document.getElementById('attach-content-file')
        this._attachPreview = document.getElementById('attach-preview')
        this._sendAttach = document.getElementById('send-attach')
        this._cancelAttach = document.getElementById('cancel-attach')
        this._attachForm = document.getElementById('attach-form')
        this._loader = document.getElementById('loader')
        this._loaderRooms = document.getElementById('loaderRooms')
        this._loaderOnline = document.getElementById('loaderOnline')
        this._searchForm = document.getElementById('search-form')
        this._searchRun = document.getElementById('search-run')
        this._sendCreateRoom = document.getElementById('send-create-room')
        this.subscribeOnEvent()
        this.enterKeyListener()
        this.clickListener()
        this.createRoomListener()
        this.attachListener()
        this._inputFileAttach.addEventListener('change', () => {
            this.showPreview()
            console.log('show')
        })
        this._chatWindow.addEventListener('scroll', (event) => {
            if(this._chatWindow.scrollHeight - this._chatWindow.scrollTop)
                if (!(this._chatWindow.scrollHeight - this._chatWindow.scrollTop <= this._chatWindow.clientHeight)) {
                    this._buttonScroll.style.display = 'block'
                    return;
                }
            this._buttonScroll.style.display = 'none'
        })

        this._buttonScroll.addEventListener('click', event => {
            this.scrollToBottom(this._chatWindow)
        })
        this._searchRun.addEventListener('click', event => {

        })

        console.log('scroll')
    }

    showPreview() {
        let file = this._inputFileAttach.files[0]
        this._attachPreview.src = URL.createObjectURL(file)
        this._attachPreview.style.display = 'block'
    }

    roomIsEquals(room, anotherRoom) {
        return Object.entries(room).toString() === Object.entries(anotherRoom).toString()
    }

    async highLightCurrentRoom(currentRoom) {
        this._roomsModels.forEach((value, key, map) => {
            // Какая то проверка
            if(this.roomIsEquals(this._currentRoom, value)) {
                key.style.backgroundColor = '#032f4f'
                key.style.pointerEvents = 'none'
                this._highLightedElement = key
                console.log('highlight')
            }
        })
    }

    createRoomListener() {
        this._sendCreateRoom.addEventListener('click', () => {
            this.createRoom()
        })
    }

    async createRoom() {
        let roomName = document.getElementById('roomNameInput').value
        let roomPrivate = document.getElementById('roomPrivateCheck')
        console.log(roomPrivate)
        let json = JSON.stringify({'room_name': roomName, 'username': this._currentUser, 'room_private': roomPrivate})
        fetch('/create-room', {
            headers: {
                "Content-Type": "application/json"
            },
            method: 'POST',
            body: json
        }).then((response) => {
            if(!response.ok)
                alert('Неудалось создать комнату')
            return response
        }).then((data => {
            console.log(data)
        })).catch(error => {
            throw new Error(`create room is invalid ${error}`)
        })
    }

    searchMessages() {
        fetch('/search-messages?' + new URLSearchParams({
            username: this._currentUser,
            query: this._searchForm.value,
        })).then((response) => {
            if(!response.ok)
                alert('Неудалось запустить поиск')
            return response.json()
        }).then(data => {
            return data
        }).catch(error => {
            throw new Error(`Search message ${error}`)
        })
    }
    clearPreview() {
        this._attachPreview.src = '#'
        this._attachPreview.style.display = 'none'
    }

    attachListener() {
        this._sendAttach.addEventListener('click', () => {
            this.clearPreview()
            console.log('clear')
        })
        this._cancelAttach.addEventListener('click', () => {
            this.clearPreview()
            console.log('clear')
        })
        this._sendAttach.addEventListener('click', () => {
            this.sendAttach()
        })
    }

    sendAttach(event) {
        event.preventDefault()
        let data = new FormData()
            data.append('attach_file', this._inputFileAttach.files[0])
            data.append('username', this._currentUser)
            data.append('text', document.getElementById('text-with-attach').value)
            data.append('room_id', this._currentRoom.id)
            fetch('/attach', {
                method: 'POST',
                body: data
            }).then(response => {
                return response.json()
            }).then(data => {
                console.log(data)
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
            if(this._currentRoom['id'] === data['room_id']) {
                this.appendMessage(data)
            }
            this._roomsModels.forEach((value, key, map) => {
                console.log(this._currentRoom, data['room_id'])
                if(value['id'] === data['room_id'] && this._currentRoom['id'] !== data['room_id']) {
                    key.innerHTML = `${key.innerHTML}+`
                }
            })
        })
        this._socket.on('new_room', data => {
            this.appendRoom(data['room'])
        })
        this._socket.on('leave', data => {
            // Если пришло увдомление о выходи, удаляем из списка html и списка
            console.log('leaved')
            this.removeUserFromOnline(data['username'])
        })
        this._socket.on('join', data => {
            this.addUserToOnlineList(data['username'], data['room'])
        })
    }

    async removeUserFromOnline(username_leaved) {
        if(!this._onlineUsers.get(username_leaved))
            return
        this._onlineListHtml.removeChild(this._onlineUsers.get(username_leaved))
        this._onlineUsers.delete(username_leaved)
    }

    async onClickRoom(element) {
        this.showLoader(this._loader)
        this._highLightedElement.style.backgroundColor = '#0a6ebd'
        this._highLightedElement.style.pointerEvents = 'auto'
        let room = this._roomsModels.get(element)
        this._currentRoom = room
        await this.highLightCurrentRoom(this._currentRoom)
        await this.getRoomHistory(room)
    }

    async getRoomHistory(room) {
        fetch(`/get-history/${room['name']}`).then((response) => {
            if(!response.ok)
                alert('Неудалось получить сообщение из комнаты')
            console.log('get-history')
            return response.json()
        }).then((data) => {
            this.hideLoader(this._loader)
            while(this._chatWindow.firstChild) {
                this._chatWindow.firstChild.remove()
            }
            data.messages.forEach(msg => {
                this.appendMessage(msg)
            })

            this.scrollToBottom(this._chatWindow)
        })

    }


    convertDate(date) {
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

    async appendMessage(data) {
        if(!data['text'])
            return
        let li = document.createElement("li");
        let username_element = document.createElement('strong',)
        username_element.appendChild(document.createTextNode(data["username"]))
        if(!data['date'])
            data['date'] = new Date().toDateString()
        li.appendChild(username_element)
        li.appendChild(document.createTextNode(` ${this.convertDate(data['date'])}`))
        li.appendChild(document.createElement('br'));
        li.appendChild(document.createTextNode(data["text"]))
        li.appendChild(document.createElement('br'));
        if(data['attachments']) {
            data['attachments'].forEach(attachment => {
                let attachmentImg = document.createElement('img')
                attachmentImg.src = attachment['link']
                attachmentImg.loading = 'lazy'
                attachmentImg.style.maxWidth = '540px'
                attachmentImg.style.minWidth = '340px'
                li.appendChild(attachmentImg)
            })
        }
        this._chatWindow.appendChild(li);
        this.scrollToBottom(this._chatWindow)
    }

    getOnlineUsers() {
        this.showLoader(this._loaderOnline)
        fetch('get-online').then(response => {
            if(!response.ok)
                throw new Error('Server is response faield')
            return response.json()
        }).then(data => {
            data.forEach(user => {
                this.hideLoader(this._loaderOnline)
                if(this.isCurrentUser(user))
                    return;
                this.addUserToOnlineList(user)
            })
        }).catch(error => {
            throw new Error(`User is invalid ${error}`)
        })
    }

    isCurrentUser(username) {
        return this._currentUser === username
    }

    addUserToOnlineList(username, room) {
        let li = document.createElement("li");
        li.id = username
        if(username === this._currentUser) {
            li.appendChild(document.createTextNode('(Вы) ' + username))
        }
        else
            li.appendChild(document.createTextNode(username));
        this._onlineListHtml.appendChild(li);
        this._onlineUsers.set(username, li);
    }

    async getCurrentUser() {
        return fetch('get-current-user').then(response => {
            if(!response.ok)
                throw new Error('Server is response faield')
            return response.json()
        }).then(data => {
            return data
        }).catch(error => {
            throw new Error(`User is invalid ${error}`)
        })
    }

    appendRoom(room) {
        console.log(room)
        let li = document.createElement("li");
        li.classList.add('room')
        li.appendChild(document.createTextNode(room["name"]))
        this._roomList.appendChild(li);
        li.addEventListener('click', (event) => {
            this.onClickRoom(event.target)
        })
        this._roomsModels.set(li, room)
    }

    async getRooms() {
        this.showLoader(this._loaderRooms)
        return fetch('get-rooms').then(response => {
            if(!response.ok)
                alert('Неудалось получить список комнат')
            return response.json()
        }).then(data => {
            this.hideLoader(this._loaderRooms)
            data.rooms.forEach(room => {
                this.appendRoom(room)
            })
            return data
        }).catch(error => {
            throw new Error(`getRooms is invalid ${error}`)
        })
    }
    showLoader(loader) {
        loader.classList.remove('d-none')
    }

    hideLoader(loader) {
        loader.classList.add('d-none')
    }
    async getHistory() {
        this.showLoader(this._loader)
        fetch(`get-history/${this._currentRoom['name']}`).then(response => {
            if(!response.ok)
                alert('Неудалось получить историю сообщений')
            return response.json()
        }).then(data => {
            this.hideLoader(this._loader)
            this._currentRoom = data
            data.messages.forEach(msg => {
                this.appendMessage(msg)
            })
            this.scrollToBottom(this._chatWindow)
        })
    }

    sendMessage() {
        let text = document.getElementById("message").value;
        let message = new Message(this._currentUser, text, Math.floor(new Date().getTime() / 1000), this._currentRoom.id)
        this._socket.emit("new_message", message.toJson());
        document.getElementById("message").value = "";
    }

    enterKeyListener() {
        document.getElementById("message").addEventListener("keyup", event => {
            if (event.key === "Enter") {
                this.sendMessage()
            }
        })
    }

    clickListener() {
        document.getElementById("send_msg").addEventListener('click', event => {
            this.sendMessage()
        })
    }

    scrollToBottom(element) {
        element.scrollTop = element.scrollHeight;
    }

}

let controller = new ChatController()
