# Code Citations

## License: unknown
https://github.com/gurchz/Moneykeeper/tree/b0b0cfd2e998d18425fbf21e5634d44726b6cb8b/templates/navbar.html

```
%}active{% endif %}" href="{{ url_for('dashboard') }}">Dashboard</a>
    </li>
    <li class="nav-item">
        <a class="nav-link {% if request
```


## License: unknown
https://github.com/mja00/swarmsmp-site/tree/61517caf0e81a11fd97531d3279b769648d9a38e/services/web/project/templates/base.html

```
auto">
    <li class="nav-item">
        <a class="nav-link {% if request.endpoint == 'index' %}active{% endif %}" href="{{ url_for('index') }}"
```


## License: unknown
https://github.com/FruitbatM/TrailRunnerTails/tree/3c9b4c9a9e9a16bccb76f317fe5c5e92aa512891/templates/base.html

```
"nav-link {% if request.endpoint == 'index' %}active{% endif %}" href="{{ url_for('index') }}">Home</a>
    </li>
    <li class="nav-
```


## License: unknown
https://github.com/Codemaster-Lohesh/Photoshop-Clone/tree/d76747e588e7f14e3637a6435786e0ad17ec79a9/photoshop/templates/layout.html

```
>
    </li>
</ul>
<ul class="navbar-nav">
    {% if current_user.is_authenticated %}
        <li class="nav-item">
            <a href="{{ url_for('logout') }}" class=
```


## License: unknown
https://github.com/PeterWorakarn/quizmate/tree/1e54ac1798fe2a7f0c6100f3982b606cda57faec/templates/includes/_navigation.html

```
">
            <a href="{{ url_for('logout') }}" class="btn btn-outline-secondary">Logout</a>
        </li>
    {% else %}
        <li class="nav-item">
            <a
```

