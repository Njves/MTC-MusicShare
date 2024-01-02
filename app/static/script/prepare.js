let validateNotBlankUsername = (username, alertBlock, event) => {
    if(username.trim() === '') {
        showError(alertBlock, 'Имя не должно быть пустое')
        event.preventDefault()
    }
}

let validateTooLongUser = (username, alertBlock, event) => {
    if(username.length > 30) {
        showError(alertBlock, 'Имя должно быть меньше 30 символов')
        event.preventDefault()
    }
}

let validateUsernameAlreadyBusy = (username, alertBlock, event) => {
    return fetch(`check-username?username=${username}`).then(response => {
        if(response.status === 409)
            showError(alertBlock, 'Пользователь с таким именем уже существует')
            event.preventDefault()
        return response.json()
    }).then(data => {
        if(data.status === 200)
            return true
        console.log(data)
    }).catch(error => {
        showError(alertBlock, `${error}`)
        event.preventDefault()
        throw new Error(`${error}`)
    })
}
let showError = (alertBlock, message) => {
    alertBlock.style.display = 'block'
    alertBlock.innerText = message
}
let hideError = (alertBlock) => {
    alertBlock.style.display = 'none'
}


let submitForm = (event) => {
    let username = document.forms[0].username.value
    let alertBlock = document.getElementById('alert')
    validateTooLongUser(username, alertBlock, event)
    validateNotBlankUsername(username, alertBlock, event)

    validateUsernameAlreadyBusy(username, alertBlock, event).then(result => {
        if(!result)
            event.preventDefault()
    })



}