
class OnlineChatView {
    #onlineWindow = $('#users-list')
    #loader = $('#loaderOnline');

    showLoader() {
        this.#loader.removeClass('d-none')
    }

    hideLoader() {
        this.#loader.addClass('d-none')
    }

    addUser(user) {
        $(`<li id="${user['username']}">${user['username']}</li>`).appendTo(this.#onlineWindow)
    }

    removeUser(user) {
        $(`#${user['username']}`).remove()
    }
}

class OnlineChatController {
    #view = new OnlineChatView();
    #usersSet = new Set()
    getOnlineUsers() {
        this.#view.showLoader()
        return fetch('get-online', {

        }).then(response => {
            if(!response.ok) {
                throw new Error('Неудалось получить список онлайн пользователей')
            }
            return response.json()
        }).then(data => {
            this.#view.hideLoader()
            data.forEach(user => {
                this.addUser(user)
            })
        }).catch(error => {
            alert(error)
        })
    }

    addUser(user) {
        let have = false
        console.log(have)
        this.#usersSet.forEach((userSet) => {
            if(user['id'] === userSet['id'])
                have = true
        })
        console.log(have, user)
        if(!have) {
            this.#usersSet.add(user)
            this.#view.addUser(user)
        }
    }

    removeUserFromOnline(user) {
        this.#view.removeUser(user)
        this.#usersSet.delete(user)
    }

}

export {OnlineChatController}