var ers = [
    
    {% for key in links %}
    {% for link in links[key] %}
    {% if key == "prime_explicit_refs" %}
    {% set er = link %}
    {% set link_name = "" %}
    {% else %}
    {% set er = link["explicit_ref"] %}
    {% set link_name = link["link_name"] %}
    {% endif %}
    {% if er.group == None %}
    {% set group = "N/A" %}
    {% else %}
    {% set group = er.group.name %}
    {% endif %}
    {
        "id": "{{ er.explicit_ref_uuid }}",
        "explicit_reference": "{{ er.explicit_ref }}",
        "group": "{{ group }}",
        "ingestion_time": "{{ er.ingestion_time }}",
        "label": "{{ key }}",
        "link_name": "{{ link_name }}"
    },
    {% endfor %}
    {% endfor %}
]
