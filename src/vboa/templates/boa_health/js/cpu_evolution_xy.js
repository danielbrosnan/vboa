
var events = [
    {% for event in events %}
    {% for usage in ["cpu_user", "cpu_nice", "cpu_system", "cpu_idle", "cpu_iowait", "cpu_irq", "cpu_softirq", "cpu_steal", "cpu_guest", "cpu_guest_nice", "cpu_usage_percentage"] %}
    {% set usage_percentage = event.eventDoubles|selectattr("name", "equalto", usage)|first|attr("value") %}
    {
        "id": "{{ event.event_uuid }}-{{ usage }}",
        "group": "{{ usage }}",
        "x": "{{ event.start.isoformat() }}",
        "y": "{{ usage_percentage }}",
        "tooltip": "<table border='1'>" +
            "<tr><td>Group</td><td>{{ usage }}</td>" +
            "<tr><td>Notification time</td><td>{{ event.start.isoformat() }}</td>" +
            "<tr><td>Value</td><td>{{ usage_percentage|round(3) }}</td>" +
            '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/{{ event.event_uuid }}">{{ event.event_uuid }}"></a></td>' +
            "</tr></table>"
    },
    {% endfor %}
    {% endfor %}
]
