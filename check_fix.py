content = open('frontend/rh/index.html', encoding='utf-8').read()
checks = {
    'Bouton type=button': 'type="button" id="btn-login"' in content,
    'Form onsubmit=return false': 'onsubmit="return false;"' in content,
    'Bouton onclick=doLogin': 'onclick="doLogin()"' in content,
    'window.location.replace': 'window.location.replace' in content,
}
for k, v in checks.items():
    print(f"{'OK' if v else 'MANQUE'} - {k}")
