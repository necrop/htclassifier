

def update_record(request, post):
    user = request.user
    userid = post.get('userid')
    mode = post.get('mode')

    if not user.username or int(userid) != int(user.id):
        return 'lfail'

    if mode == 'password':
        current_password = post.get('password', '').strip()
        new_password1 = post.get('newpassword1', '').strip()
        new_password2 = post.get('newpassword2', '').strip()
        if not new_password1 or new_password1 != new_password2:
            return 'pfail'
        elif not user.check_password(current_password):
            return 'pfail'
        else:
            user.set_password(new_password1)
            user.save()
            return 'psuccess'

    elif mode == 'details':
        user.first_name = post.get('firstname').strip()
        user.last_name = post.get('lastname').strip()
        user.email = post.get('email').strip()
        user.save()
        return 'dsuccess'
