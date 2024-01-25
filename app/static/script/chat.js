import {OnlineChatController} from "./onlineChat.js";
const toastLiveExample = document.getElementById('liveToast')
const toastText = document.getElementById('toastBody')
function showToast(header=null, text) {
    if (header) {
        $('.me-auto').html(header).css('color', 'green')
    }
    toastText.innerHTML = text
    const toast = new bootstrap.Toast(toastLiveExample)
    toast.show()
}



class ChatController {
    _socket = null;
    #onlineChatController = new OnlineChatController();
    _currentUser = null;
    notificationSound = new Audio("/content/notify")
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
    #count = 20
    #offset = 0
    attachedFiles = []
    #searchMode = false
    constructor() {
        this.getCurrentUser().then(user => {
            this._currentUser = user
            this._socket = io({autoConnect: true, query: {
                    'user_id': user.id
                }});
            showToast('Сервер','Вы подключены к серверу')
            this.getRooms().then(rooms => {
                this.subscribeOnEvent()
                let currentRoom = parseInt(localStorage.getItem('userRoom'))
                this.highLightCurrentRoom(this._currentRoom)
                this._initRoom = currentRoom
                this._roomsModels.forEach((value, key, map) => {
                    if(value['id'] === parseInt(this._initRoom)) {
                        this.onClickRoom(key)
                    }
                })

            })
        })
        $('#loadingMessage').hide()
        this._chatWindow = document.getElementById("chat-messages");
        this._buttonScroll = document.getElementById('button_scroll_down')
        this._roomsModels = new Map()
        this._roomList = document.getElementById('roomsList')
        this._inputFileAttach = document.getElementById('attach-content-file')
        this._sendAttach = document.getElementById('send-attach')
        this._cancelAttach = document.getElementById('cancel-attach')
        this._attachForm = document.getElementById('attachForm')
        this._loader = document.getElementById('loader')
        this._loaderRooms = document.getElementById('loaderRooms')
        this._searchForm = document.getElementById('search-form')
        this._searchRun = document.getElementById('search-run')
        this._sendCreateRoom = document.getElementById('send-create-room')
        this.#onlineChatController.getOnlineUsers()

        $('.control-panel').css('pointer-events', 'none')

        this.enterKeyListener()
        this.clickListener()
        this.createRoomListener()
        this.attachListener()
        $('attach-preview').change(function() {
            // let file = $('attach-content-file').prop('files')[0]
            // this.attr('src', URL.createObjectURL(file))
            // this.show()
        })
        this.hideLoader(this._loader)
        this._chatWindow.addEventListener('scroll', (event) => {
            if(this._chatWindow.scrollTop === 0 && !this.#searchMode) {
                this.getRoomHistory(this._currentRoom, false)
            }
            if(this._chatWindow.scrollHeight - this._chatWindow.scrollTop) {
                if (!(this._chatWindow.scrollHeight - this._chatWindow.scrollTop <= this._chatWindow.clientHeight)) {
                    this._buttonScroll.style.display = 'block'
                    return;
                }
            }
            this._buttonScroll.style.display = 'none'
        })
        this._buttonScroll.addEventListener('click', event => {
            this.scrollToBottom(this._chatWindow)
        })
        this._searchRun.addEventListener('click', event => {
            this._highLightedElement.style.backgroundColor = '#0a6ebd'
            this._highLightedElement.style.pointerEvents = 'auto'
            this.searchMessages()
        })
        Dropzone.autoDiscover = false
        // this._sendAttach.addEventListener('click', () => {
        //     this.sendMessageWithAttach()
        //
        // })

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
        this.removeRoomListener()

    }
    async removeRoomListener() {
        $("#removeRoom").on('click', async () => {
            let roomId = this._currentRoom.id
            if (!roomId) {
                showToast('Ошибка', 'Выберите комнату')
            }
            let response = await fetch('/room/' + roomId, {
                method: 'DELETE'
            })
            if (!response.ok) {
                showToast('Ошибка', 'Неудалось удалить комнату')
                return
            }
            showToast('Успех', 'Комната удалена')
        })
    }
    roomIsEquals(room, anotherRoom) {
        return Object.entries(room).toString() === Object.entries(anotherRoom).toString()
    }

    async highLightCurrentRoom(room) {
        if(!this._currentRoom)
            return;
        this._roomsModels.forEach((value, key, _) => {
            // Какая то проверка
            if(this.roomIsEquals(room, value)) {
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
        let json = JSON.stringify({'name': roomName, 'room_private': roomPrivate})
        fetch('/room', {
            headers: {
                "Content-Type": "application/json"
            },
            method: 'POST',
            body: json
        }).then((response) => {
            if(!response.ok) {
                $('#alertRoom').show()
                if(response.status === 409)
                    $('#alertRoom').html('Вы не можете создать более 3-х комнат')
                else if(response.status === 400)
                    $('#alertRoom').html('Название комнаты не должно превышать 18 символов и быть длинее 4-х символов')
                throw new Error('Error')
            }
            return response
        }).then((data => {
            $('#alertRoom').hide()
            $('#cancel-create-room').trigger({'type': 'click'})
        })).catch(error => {
            throw new Error(`create room is invalid ${error}`)
        })
    }

    searchMessages() {
        fetch('/messages/search?' + new URLSearchParams({
            query: this._searchForm.value,
            room_id: this._currentRoom.id
        })).then((response) => {
            if(!response.ok) {
                if(response.status === 400)
                    showToast('Ошибка', 'Невозможно выполнить операцию поиска')
                    throw new Error(response.json()['error'])
            }
            return response.json()
        }).then(data => {
            this.#searchMode = true
            $('#message-list-empty').html('Результат поиска ' + data.length + ' сообщение').show()
            $('.control-panel').hide()
            while (this._chatWindow.firstChild) {
                this._chatWindow.firstChild.remove()
            }
            data.forEach(message => {
                this.appendMessage(message, true)
            })

            return data
        }).catch(error => {
            throw new Error(`Search message ${error}`)
        })
    }
    clearPreview() {
        // this._attachPreview.src = '#'
        // this._attachPreview.style.display = 'none'
    }

    attachListener() {
        this._sendAttach.addEventListener('click', () => {
            this.clearPreview()
        })
        this._cancelAttach.addEventListener('click', () => {
            this.clearPreview()
        })
        this._sendAttach.addEventListener('click', () => {
            // this.sendAttach()
        })
    }

    sendAttach() {
        let data = new FormData()
        data.append('room_id', this._currentRoom.id)
        fetch('/message/attach', {
            method: 'POST',
            body: data
        }).then(response => {
            if(!response.ok) {
                throw new Error('Неудалось')
            }
            return response.json()
        }).catch(error => {
            showToast('Неудалось отправить сообщение')
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
            $('#loadingMessage').hide()
            $('.send-img').show()
            if(data['username'] !== this._currentUser.username)
                this.notificationSound.play();
            if(this._currentRoom['id'] === data['room_id']) {
                this.appendMessage(data, true)
            }
            this.scrollToBottom(this._chatWindow)

        })
        this._socket.on('on_delete', data => {

        })
        this._socket.on('on_delete_room', data => {
            this._roomsModels.forEach((value, key, map) => {
                if(value['id'] === data['id']) {
                    key.remove()
                }
            })
        })
        this._socket.on('notify', data => {
            this._roomsModels.forEach((value, key, map) => {
                if(value.id === this._currentRoom.id)
                    return
                if(value.id === data.room_id) {
                    showToast('Новое сообщение', 'Новое сообщение в комнате ' + value.name)
                }
            })

            if(!this._currentRoom)
                return
            this._roomsModels.forEach((value, key, map) => {
                if(value['id'] === data['room_id'] && this._currentRoom['id'] !== data['room_id']) {
                    key.innerHTML = `${key.innerHTML}+`
                }
            })
        })
        this._socket.on('new_room', data => {
            this.appendRoom(data)
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
	window.history.pushState('room', 'python', '127.0.0.1/python')
        this.#offset = 0
        this.#count = 20
        this.showLoader(this._loader)
        $('.control-panel').hide()
        $('#message-list-empty').hide()
        $('#search-form').val('')
        $('.control-panel').css('pointer-events', 'auto')
        let room = this._roomsModels.get(element)
        $('#mainText').html(`Чатик (${room.name})`)
        localStorage.setItem('userRoom', room.id)
        if(!this._currentRoom) {
            this._socket.emit('join', {'id': room.id})
        } else {
            this._socket.emit('leave', {'id': this._currentRoom.id})
            this._socket.emit('join', {'id': room.id})
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
        $('.control-panel').show()
    }

    async getRoomHistory(room, change=true) {
        fetch(`/room/${room['id']}?offset=${this.#offset}&count=${this.#count}`).then((response) => {
            if(!response.ok)
                showToast('Ошибка', 'Неудалось получить сообщение из комнаты')
            return response.json()
        }).then((data) => {
            this.hideLoader(this._loader)
            if(change) {
                while (this._chatWindow.firstChild) {
                    this._chatWindow.firstChild.remove()
                }
            }

            if(data.messages.length > 0) {
                $('#message-list-empty').hide()
                if(this.#offset !== 0) {
                    let child = this._chatWindow.firstChild.parentNode
                    let p = document.createElement('p')
                    p.appendChild(document.createTextNode('Старые сообщения'))
                    p.style.textAlign = 'center'
                    child.prepend(p)
                }
                this.#offset += this.#count

            }
            if(data.messages.length === 0 && this._chatWindow.children.length === 0) {
                $('#message-list-empty').show().html('В комнате нет сообщений')
            }
            data.messages.forEach(msg => {
                this.appendMessage(msg)
            })
            if(change) {
                this.scrollToBottom(this._chatWindow)
            }

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
                showToast('Ошибка', 'Неудалось изменить сообщение')
            return response.json()
        }).then(data => {
            this.editElement(element, data)
        })
    }
    async editElement(element, data){
        let convertedDate = this.convertDate(data['date'])

    }

    async appendMessage(data, append=false) {
        if(this._chatWindow.children.length === 0) {
            $('#message-list-empty').hide()
        }
        if(!data['text'] && !data['attachments'])
            return
        let li = document.createElement("li");
        let convertedDate = this.convertDate(data['date'])
        let username_el = $(`<strong>${data['user']['username']}</strong>`).css('color', data['user']['color']).appendTo(li)
        $(`<span> ${convertedDate}</span>`).appendTo(li)
        if(this._currentUser['username'] === data['user']['username']) {
            $("<button class='btn btn-outline-danger m-1 p-1'>Удалить</button>")
                .on('click', () => {
                    this.deleteMessage(li, data);
                })
                .appendTo(li);
            // $("<button class='btn btn-outline-primary m-1 p-1'>Редактировать</button>")
            //     .on('click', () => {
            //     })
            //     .appendTo(li);
        }
        $(`<br/><span id=${data['id']}>${data['text']}</span>`).addClass('message-text').appendTo(li)

        if(data['attachments']) {
            let div = document.createElement('div')
            div.classList.add('d-flex')
            div.classList.add('flex-wrap')
            data['attachments'].forEach(attachment => {
                let attachmentImg = document.createElement('img')
                attachmentImg.src = attachment['link']
                attachmentImg.loading = 'lazy'
                attachmentImg.width = 200
                attachmentImg.classList.add('m-1')
                div.appendChild(attachmentImg)
            })
            li.appendChild(div)
        }
        if(append) {
            this._chatWindow.append(li)
        } else {
            this._chatWindow.prepend(li);
        }

    }

    async getCurrentUser() {
        return fetch('user/current').then(response => {
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
        let div = document.createElement('div')
        let li = document.createElement("li")
        li.classList.add('room')
        li.append(document.createTextNode(`${room['name']}`))
        div.appendChild(li)
        this._roomList.appendChild(div)

        li.addEventListener('click', (event) => {
            this.onClickRoom(event.target)
        })
        this._roomsModels.set(li, room)
    }

    async getRooms() {
        this.showLoader(this._loaderRooms)
        return fetch('/rooms').then(response => {
            if(!response.ok)
                showToast('Ошибка','Неудалось получить список комнат')
            return response.json()
        }).then(data => {
            this.hideLoader(this._loaderRooms)
            data.forEach((room) => {
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
                showToast('Ошибка', 'Неудалось удалить сообщение')
                return
            }
            return response
        }).then(data => {
            if(data.ok) {
                $(element).hide(500, () => {
                    $(element).remove()
                    if(this._chatWindow.children.length === 0) {
                        $('#message-list-empty').show()
                    }
                })
                this._socket.emit('delete', message)

            }
        })
    }

    sendMessageWithAttach() {
        $('#loadingMessage').show()
        $('.send-img').hide()
        let text = $('#attachText').val()
        let msg = {
            text: text,
            attachments: this.attachedFiles,
            user_id: this._currentUser.id,
            room_id: this._currentRoom.id
        }
        fetch('/message/attach', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(msg)
        }).then(response => {
            if(!response.ok) {
                throw new Error('Неудалось')
            }
            this.attachedFiles = []
            return response.json()
        }).catch(error => {
            showToast('Неудалось отправить сообщение')
        })
    }

    sendMessage() {
        $('#loadingMessage').show()
        $('.send-img').hide()
        let text = document.getElementById("message").value;
        if(text.trim().length <= 0)
            return;
        let message = {
            user: this._currentUser,
            text: text,
            date: Math.floor(new Date().getTime() / 1000),
            room_id: this._currentRoom.id
        }
        this._socket.emit("new_message", JSON.stringify(message));
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
$(document).ready(function () {
    $('#attachForm').dropzone({
        autoProcessQueue: true, // Отключаем автоматическую обработку файлов
        url: '/upload',
        paramName: "file", // Имя параметра, которое будет отправлено на сервер
        maxFilesize: 5, // Максимальный размер файла в мегабайтах
        acceptedFiles: 'image/*', // Принимаем только изображения
        addRemoveLinks: true, // Добавляем ссылку для удаления файла
        init: function () {
            var myDropzone = this;
            // Нажатие кнопки "Отправить"
            document.getElementById("send-attach").addEventListener("click", function (e) {
                e.preventDefault();
                myDropzone.removeAllFiles(true)
                controller.sendMessageWithAttach()
            });

            // Удаление файла из Dropzone и предпросмотр
            myDropzone.on("removedfile", function (file) {
                // Удаление файла из сервера, если необходимо
            });
            myDropzone.on("errormultiple", function (files, response) {
                showToast('Ошибка', `Неудалось загрузить файлы ${response.error}`)
            })
            myDropzone.on('sending', function() {
                controller._sendAttach.disabled = true
            })
            myDropzone.on("success", function (files, response) {
                showToast('Успех', `Файлы успешно отправлены`)
                controller.attachedFiles.push(response[0])
                controller._sendAttach.disabled = false
            })
        }
    })
})
