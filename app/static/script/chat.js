import {ChatView} from './chatView.js';
import {OnlineChatController} from "./onlineChat.js";
const toastTrigger = document.getElementById('liveToastBtn')
const toastLiveExample = document.getElementById('liveToast')
const toastText = document.getElementById('toastBody')
function showToast(toastText) {
    if (toastTrigger) {
        toastTrigger.addEventListener('click', () => {
            toastText.innerHTML = toastText
            const toast = new bootstrap.Toast(toastLiveExample)

            toast.show()
        })
    }
}


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
        return JSON.stringify({"user": this._senderUsername, 'text': this._text, 'date': this._date, 'room_id': this._roomId})
    }

    fromJson(string) {
        let jsonObject = JSON.parse(string)
        return new Message(jsonObject['user'], jsonObject['text'], jsonObject['date'], jsonObject['room_id'])
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
    #onlineChatController = new OnlineChatController();
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
    _searchForm = null;
    _searchRun = null;
    _roomsModels = null;
    _currentRoom = null;
    _highLightedElement = null;
    _sendCreateRoom = null;
    _initRoom = null;
    _messagePart = 1
    constructor() {
        this._socket = io({autoConnect: false, query: {
                'user_id': 8
            }});

        this.getCurrentUser().then(user => {
            this._currentUser = user
            this.getRooms().then(rooms => {
                this.highLightCurrentRoom(this._currentRoom)
                if(Cookies.get('current_room')) {
                    this._initRoom = Cookies.get('current_room')
                    this._roomsModels.forEach((value, key, map) => {
                        if(value['id'] === parseInt(this._initRoom)) {
                            this.onClickRoom(key)
                        }
                    })
                }
            })
        })

        this._chatWindow = document.getElementById("chat-messages");
        this._buttonScroll = document.getElementById('button_scroll_down')
        this._socket.connect()
        this._roomsModels = new Map()
        this._roomList = document.getElementById('rooms-list')
        this._inputFileAttach = document.getElementById('attach-content-file')
        this._sendAttach = document.getElementById('send-attach')
        this._cancelAttach = document.getElementById('cancel-attach')
        this._attachForm = document.getElementById('attach-form')
        this._loader = document.getElementById('loader')
        this._loaderRooms = document.getElementById('loaderRooms')
        this._searchForm = document.getElementById('search-form')
        this._searchRun = document.getElementById('search-run')
        this._sendCreateRoom = document.getElementById('send-create-room')
        this.#onlineChatController.getOnlineUsers()
        $('.control-panel').css('pointer-events', 'none')
        this.subscribeOnEvent()
        this.enterKeyListener()
        this.clickListener()
        this.createRoomListener()
        this.attachListener()
        $('attach-preview').change(function() {
            let file = $('attach-content-file').prop('files')[0]
            this.attr('src', URL.createObjectURL(file))
            this.show()
        })
        this.hideLoader(this._loader)
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
        $('#roomPrivateCheck').change(function() {
            // Check if the checkbox is checked
            if ($(this).is(':checked')) {
                // If checked, add an input element to the container
                $('.modal-body').append(`<div class="form-group room-password-container">
                        <label for="roomPasswordInput">Пароль от комнаты</label>
                        <input type="text" class="form-control" id="roomPasswordInput" placeholder="Пароль от комнаты">
                    </div>`);
            } else {
                // If unchecked, remove the input element
                $('.room-password-container').remove();
            }
        });
    }

    roomIsEquals(room, anotherRoom) {
        return Object.entries(room).toString() === Object.entries(anotherRoom).toString()
    }

    async highLightCurrentRoom() {
        if(!this._currentRoom)
            return;
        this._roomsModels.forEach((value, key, map) => {
            // Какая то проверка
            if(this.roomIsEquals(this._currentRoom, value)) {
                key.style.backgroundColor = '#032f4f'
                key.style.pointerEvents = 'none'
                this._highLightedElement = key
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
        })
        this._cancelAttach.addEventListener('click', () => {
            this.clearPreview()
        })
        this._sendAttach.addEventListener('click', () => {
            this.sendAttach()
        })
    }

    sendAttach(event) {
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

        })
        this._socket.on('on_delete', data => {

        })
        this._socket.on('notify', data => {
            if(!this._currentRoom)
                return
            this._roomsModels.forEach((value, key, map) => {
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
            this.#onlineChatController.removeUserFromOnline(data)
        })
        this._socket.on('join', data => {
            this.#onlineChatController.addUser(data)
        })
    }

    async onClickRoom(element) {
        this.showLoader(this._loader)
        $('#message-list-empty').hide()
        $('.control-panel').css('pointer-events', 'auto')
        let room = this._roomsModels.get(element)
        if(!this._currentRoom) {
            this._socket.emit('join', {'room_id': room.id})
        } else {
            this._socket.emit('leave', {'room_id': this._currentRoom.id})
            this._socket.emit('join', {'room_id': room.id})
        }

        this._currentRoom = room
        if(!this._highLightedElement)
            this._highLightedElement = element
        if(this._highLightedElement) {
            this._highLightedElement.style.backgroundColor = '#0a6ebd'
            this._highLightedElement.style.pointerEvents = 'auto'
            await this.highLightCurrentRoom(this._currentRoom)
        }
        await this.getRoomHistory(room)
    }

    async getRoomHistory(room) {
        fetch(`/get-room/${room['id']}/${this._messagePart}`).then((response) => {
            if(!response.ok)
                alert('Неудалось получить сообщение из комнаты')
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

    async editMessage(element, message) {
        message['text'] = 'хуй' + element.toString()
        return fetch(`message/${message.id}`, {
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'PUT',
            body: JSON.stringify(message)
        }).then((response) => {
            if(!response.ok)
                alert('Неудалось изменить сообщение')
            return response.json()
        }).then(data => {
            this.editElement(element, data)
        })
    }
    async editElement(element, data){
        let convertedDate = this.convertDate(data['date'])

    }

    async appendMessage(data) {
        if(!data['text'] && !data['attachments'])
            return
        let li = document.createElement("li");
        let convertedDate = this.convertDate(data['date'])
        let username_el = $(`<strong>${data['user']['username']}</strong>`).css('color', data['user']['color']).appendTo(li)
        $(`<span> ${convertedDate}</span>`).appendTo(li)
        if(this._currentUser['username'] === data['user']['username']) {
            $("<button class='btn btn-outline-danger m-1 p-1'>Удалить</button>")
                .on('click', () => {
                    console.log(data);
                    this.deleteMessage(li, data);
                })
                .appendTo(li);
            $("<button class='btn btn-outline-primary m-1 p-1'>Редактировать</button>")
                .on('click', () => {
                    // this.editMessage(li, data)
                    $(`#${data['id']}`).hide
                })
                .appendTo(li);
        }
        $(`<br/><span id=${data['id']}>${data['text']}</span>`).addClass('message-text').appendTo(li)
        if(data['attachments']) {
            data['attachments'].forEach(attachment => {
                let attachmentImg = document.createElement('img')
                attachmentImg.src = attachment['link']
                attachmentImg.loading = 'lazy'
                attachmentImg.style.maxWidth = '540px'
                attachmentImg.style.minWidth = '340px'
                li.appendChild(document.createElement('br'));
                li.appendChild(attachmentImg)
            })
        }
        this._chatWindow.appendChild(li);
        this.scrollToBottom(this._chatWindow)
    }

    isCurrentUser(username) {
        return this._currentUser === username
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

        let li = document.createElement("li")
        li.classList.add('room')
        li.append(document.createTextNode(`${room['name']}`))
        this._roomList.appendChild(li)
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

    async deleteMessage(element, message) {
        return fetch(`message/${message['id']}`, {
            headers: {
                "Content-Type": "application/json"
            },
            method: 'DELETE',
            body: JSON.stringify({'username': this._currentUser})
        }).then(response => {
            if(!response.ok) {
                alert('Неудалось удалить сообщение')
                return
            }
            return response
        }).then(data => {
            if(data.ok) {
                $(element).hide(500, () => $(element).remove())
                this._socket.emit('delete', message)
            }
        })
    }

    sendMessage() {
        let text = document.getElementById("message").value;
        console.log(text.trim().length)
        if(text.trim().length <= 0)
            return;
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
