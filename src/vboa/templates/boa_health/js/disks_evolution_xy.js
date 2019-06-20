
var events = [
    {% for event in events %}
    {% set disk_mountpoints = event.eventTexts|selectattr("name", "equalto", "disk_mountpoint")|map(attribute="value")|list %}
    {% for disk_mountpoint in disk_mountpoints %}
    {% set disk_usage = event.eventDoubles|selectattr("name", "equalto", disk_mountpoint.replace("/", "_") + "_usage_percentage")|first|attr("value") %}
    {
        "id": "{{ event.event_uuid }}-{{ disk_mountpoint }}-disk-usage",
        "group": "{{ disk_mountpoint }}",
        "x": "{{ event.start.isoformat() }}",
        "y": "{{ disk_usage }}",
        "tooltip": "<table border='1'>" +
            "<tr><td>Group</td><td>{{ disk_mountpoint }}</td>" +
            "<tr><td>Notification time</td><td>{{ event.start.isoformat() }}</td>" +
            "<tr><td>Value</td><td>{{ disk_usage|round(3) }}</td>" +
            '<tr><td>Details</td><td><a href="/eboa_nav/query-event-links/{{ event.event_uuid }}">{{ event.event_uuid }}"></a></td>' +
            "</tr></table>"
    },
    {% endfor %}
    {% endfor %}
]
