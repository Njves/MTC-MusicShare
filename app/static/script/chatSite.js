const toastTrigger = document.getElementById('liveToastBtn')
const toastLiveExample = document.getElementById('liveToast')
const toastText = document.getElementById('toastBody')

function showToast(text) {
    toastText.innerHTML = text
    toastText.style.color = 'green'
    const toast = new bootstrap.Toast(toastLiveExample)
    toast.show()
}

class OnlineUserController {
    #view = document.getElementById('usersList')
    #chatSocket = null;

    constructor(chatSocket) {
        this.#chatSocket = chatSocket
        this.subscribe()
    }

    createUserLi(user) {
        let li = document.createElement('li')
        let textNode = document.createTextNode(user.username)
        li.appendChild(textNode)
        li.style.color = user.color
        li.id = user.id
        return li
    }

    addUser(user) {
        this.#view.appendChild(this.createUserLi(user))
    }

    removeUser(user) {
        let userElement = document.getElementById(user.id)
        userElement.remove()
    }

    subscribe() {
        this.#chatSocket.socket.on('join', data => {
            this.addUser(data)
            if(data.id === this.#chatSocket.currentUser.id)
                return
            showToast(`Пользователь ${data.username} вошел`)
        })
        this.#chatSocket.socket.on('leave', data => {
            this.removeUser(data)
        })
    }
}

class RoomController {
    #view = document.getElementById('roomsList')
    room = null;
    #chatSocket = null;

    constructor(chatSocket) {
        this.#chatSocket = chatSocket
        this.getCurrentRoom().then(room => {
            this.room = room
            this.joinRoom(room)
        })

    }

    joinRoom(room) {
        this.#chatSocket.socket.emit('join', {'id': room.id})
    }

    getCurrentRoom() {
        return fetch('/room').then(response => {
            if(!response.ok) {
                showToast('Неудалось получить текущую комнату')
            }
            return response.json()
        }).then(room => {
            return room
        })
    }

}

class MessageController {
    #view = document.getElementById('chat-messages')
    #sendMessageButton = document.getElementById('sendMessage')
    #inputMessage = document.getElementById("message")
    #window = document.getElementById('chat-messages')
    #buttonScroll = document.getElementById('buttonScrollDown')
    #roomController = null
    #chatSocket = null;

    constructor(roomController, chatSocket) {
        this.#roomController = roomController
        this.#chatSocket = chatSocket
        this.subscribe()
        this.scrollToBottom(this.#window)
    }


    createMessageOwnerElement(message) {
        let div = document.createElement('div')
        let li = document.createElement('li')
        let strong = document.createElement('strong')
        strong.style.color = message.user.color
        strong.appendChild(document.createTextNode(message.user.username))
        li.appendChild(strong)
        li.appendChild(document.createTextNode(` ${message.date}`))
        let removeButton = document.createElement('a')
        removeButton.classList.add('btn')
        removeButton.classList.add('btn-danger')
        removeButton.classList.add('p-0')
        removeButton.appendChild(document.createTextNode('Удалить'))
        removeButton.addEventListener('click', () => {

        })
        li.appendChild(removeButton)
        div.appendChild(li)
        let liText = document.createElement('li')
        liText.appendChild(document.createTextNode(message.text))
        liText.style.paddingLeft = '4px'
        div.appendChild(liText)
        return div
    }

    createMessageElement(message) {
        if(this.#chatSocket.currentUser) {
            return this.createMessageOwnerElement(message)
        }
        let div = document.createElement('div')
        let li = document.createElement('li')
        let strong = document.createElement('strong')
        strong.style.color = message.user.color
        strong.appendChild(document.createTextNode(message.user.username))
        li.appendChild(strong)
        li.appendChild(document.createTextNode(` ${message.date}`))
        div.appendChild(li)
        let liText = document.createElement('li')
        liText.appendChild(document.createTextNode(message.text))
        liText.style.paddingLeft = '4px'
        div.appendChild(liText)
        return div
    }

    addMessage(message) {
        this.#view.appendChild(this.createMessageElement(message))
        this.scrollToBottom(this.#window)
    }

    sendMessage(room) {
        let message = {
            text: this.#inputMessage.value,
            date: Math.floor(new Date().getTime() / 1000),
            room_id: room.id
        }
        this.#chatSocket.socket.emit('new_message', JSON.stringify(message))
    }

    scrollToBottom(element) {
        element.scrollTop = element.scrollHeight;
    }

    subscribe() {
        this.#chatSocket.socket.on("chat", data => {
            this.addMessage(data)
        })

        this.#sendMessageButton.addEventListener('click', () => {
            this.sendMessage(this.#roomController.room)
        })
        this.#window.addEventListener('scroll', () => {
            if(this.#window.scrollHeight - this.#window.scrollTop)
                if (!(this.#window.scrollHeight - this.#window.scrollTop <= this.#window.clientHeight)) {
                    this.#buttonScroll.style.display = 'block'
                    return;
                }
            this.#buttonScroll.style.display = 'none'
        })
        this.#buttonScroll.addEventListener('click', () => {
            this.scrollToBottom(this.#window)
        })
    }
}

class Chat {
    #currentUser = null
    #roomController = null
    #chatMessageController = null
    #onlineUserController = null
    #chatSocket = null

    constructor() {
        this.getCurrentUser().then(user => {
            this.#currentUser = user
            this.#chatSocket = new ChatSocket(this.#currentUser)
            this.#onlineUserController = new OnlineUserController(this.#chatSocket)
            this.#roomController = new RoomController(this.#chatSocket)
            this.#chatMessageController = new MessageController(this.#roomController, this.#chatSocket)

        })
    }
     getChatMessageController() {
        return this.#chatMessageController
    }
    getCurrentUser() {
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
}

class ChatSocket {
    socket = null;
    currentUser = null;
    constructor(currentUser) {
        this.currentUser = currentUser
        this.socket = io({autoConnect: true, query: {
                'user_id': this.currentUser.id
            }});
        this.subscribeOnEvent()
        showToast('Вы подключены к серверу')

    }


    subscribeOnEvent() {
        this.socket.on("connect", () => {

        })
        this.socket.on('disconnect', (reason) => {
            showToast('Вы отключились от сервера')
            if (reason === "io server disconnect") {
                // the disconnection was initiated by the server, you need to reconnect manually
                this.socket.connect();
            }
        })

        this.socket.on('on_delete', data => {

        })
        this.socket.on('notify', data => {

        })
        this.socket.on('new_room', data => {

        })

    }
}
let chat = new Chat()
export {chat}