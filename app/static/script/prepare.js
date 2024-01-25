
function onLoginSubmit() {
    event.preventDefault()
    let login_obj = {'username': $('#username').val(),
        'password': $('#password').val(),
        'color': $('#color').val() }
    let login_json = JSON.stringify(login_obj)
    $('.login-btn').css("pointer-events","none");
    fetch('/login', {
        mode: 'cors',
        headers: {
            'Content-Type': 'application/json',
            'Access-Control-Expose-Headers': 'Location'

        },

        redirect: 'follow',
        method: 'POST',
        body: login_json
    }).then(response => {
        if(!response.redirected) throw response.json()
        return response
    }).then(response => {
        $('.login-btn').css("pointer-events","auto");
        window.location.href = response.url
    }).catch(e => {
        $('.login-btn').css("pointer-events","auto");
        e.then(data => {
            if(data.error)
                $('#alert').text(data.error).show()
        })
    })
}

function onRegisterSubmit() {
    event.preventDefault()
    let regObj = {'username': $('#reg_username').val(),
        'password': $('#reg_password').val()}
    let regJson = JSON.stringify(regObj)
    $('.register-btn').css("pointer-events","none");
    fetch('/register', {
        headers: {
            'Content-Type': 'application/json'
        },
        redirect: 'follow',
        method: 'POST',
        body: regJson
    }).then(response => {
        if(!response.ok) throw response.json()
        window.location.href = response.url
        $('.register-btn').css("pointer-events","auto");
        return response
    }).catch(e => {
        $('.register-btn').css("pointer-events","auto");
        e.then(data => {
            $('#reg_alert').text(data.error).show()
        })
    })
}
