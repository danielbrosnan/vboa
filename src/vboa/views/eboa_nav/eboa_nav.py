"""
EBOA navigation section definition

Written by DEIMOS Space S.L. (dibb)

module vboa
"""
# Import python utilities
import sys
import json
from distutils import util
import shlex
from subprocess import Popen, PIPE
import tempfile
import shutil

# Import flask utilities
from flask import Blueprint, flash, g, current_app, redirect, render_template, request, url_for, send_from_directory
from flask_debugtoolbar import DebugToolbarExtension
from flask import jsonify

# Import eboa utilities
from eboa.engine.query import Query
import eboa.engine.engine as eboa_engine
from eboa.engine.engine import Engine
import eboa.engine.alerts as eboa_alerts

# Import auxiliary functions
from eboa.triggering.eboa_triggering import get_triggering_conf
from vboa.functions import set_specific_alert_filters

# Import vboa security
from vboa.security import auth_required, roles_accepted

bp = Blueprint("eboa_nav", __name__, url_prefix="/eboa_nav")
query = Query()
engine = Engine()

@bp.route("/", methods=["GET"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def navigate():
    """
    Initial panel for the EBOA navigation functionality.
    """
    return render_template("eboa_nav/query_events.html")

@bp.route("/query-events", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_events_and_render():
    """
    Query events and render.
    """
    current_app.logger.debug("Query events and render")
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
        filters["offset"] = [""]

        if "query_events" in filters:
            events = query_events(filters)
            show = define_what_to_show_events(filters)
            events_geometries = []
            if show["map"]:
                events_geometries = [{"event": event, "geometries": engine.geometries_to_wkt(event.eventGeometries)} for event in events if len(event.eventGeometries) > 0]
            # end if        

            return render_template("eboa_nav/events_nav.html", events=events, events_geometries=events_geometries, show=show, filters=filters)
        else:
            event_alerts = query_event_alerts(filters)
            return render_template("eboa_nav/event_alerts_nav.html", alerts=event_alerts, filters=filters)
        # end if
    
    # end if
    return render_template("eboa_nav/query_events.html")

@bp.route("/query-events-pages", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_events_pages():
    """
    Query events using pages and render.
    """
    current_app.logger.debug("Query events using pages and render")
    filters = request.json
    events = query_events(filters)
    show = define_what_to_show_events(filters)
    events_geometries = []
    if show["map"]:
        events_geometries = [{"event": event, "geometries": engine.geometries_to_wkt(event.eventGeometries)} for event in events if len(event.eventGeometries) > 0]
    # end if        

    return render_template("eboa_nav/events_nav.html", events=events, events_geometries=events_geometries, show=show, filters=filters)

def define_what_to_show_events(filters):
    """
    Function to define what to show for events
    """
    show = {}
    show["timeline"]=True
    if not "show_timeline" in filters:
        show["timeline"] = False
    # end if
    show["map"]=True
    if not "show_map" in filters:
        show["map"] = False
    # end if        

    return show

@bp.route("/query-events-by-er/<string:er>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_events_by_er(er):
    """
    Query events associated to the explicit reference received.
    """
    current_app.logger.debug("Query events by explicit reference")
    show = {}
    show["timeline"]=True
    show["map"]=True
    filters = {}
    filters["offset"] = [""]
    filters["limit"] = ["100"]

    events = query.get_events(explicit_refs={"filter": [er], "op": "in"})

    events_geometries = []
    events_geometries = [{"event": event, "geometries": engine.geometries_to_wkt(event.eventGeometries)} for event in events if len(event.eventGeometries) > 0]

    return render_template("eboa_nav/events_nav.html", events=events, events_geometries=events_geometries, show=show, filters=filters)

@bp.route("/query-events-by-source-uuid/<string:source_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_events_by_source_uuid(source_uuid):
    """
    Query events associated to the source corresponding to the UUID received.
    """
    current_app.logger.debug("Query events by source uuid")
    show = {}
    show["timeline"]=True
    show["map"]=True
    filters = {}
    filters["offset"] = [""]
    filters["limit"] = ["100"]

    events = query.get_events(source_uuids={"filter": [source_uuid], "op": "in"})

    events_geometries = []
    events_geometries = [{"event": event, "geometries": engine.geometries_to_wkt(event.eventGeometries)} for event in events if len(event.eventGeometries) > 0]

    return render_template("eboa_nav/events_nav.html", events=events, events_geometries=events_geometries, show=show, filters=filters)

def query_events(filters):
    """
    Query events.
    """
    current_app.logger.debug("Query events")

    kwargs = set_filters_for_query_events_or_event_alerts(filters)

    events = query.get_events(**kwargs)

    return events

def query_event_alerts(filters):
    """
    Query event alerts.
    """
    current_app.logger.debug("Query event alerts")

    event_kwargs = set_filters_for_query_events_or_event_alerts(filters)

    alert_kwargs = set_specific_alert_filters(filters)

    kwargs = {**event_kwargs, **alert_kwargs}

    event_alerts = query.get_event_alerts(**kwargs)

    return event_alerts

def set_filters_for_query_events_or_event_alerts(filters):
    """
    Set filter for query events or query event alerts.
    """
    kwargs = {}

    # Wether is query event or query event alerts
    ingestion_time_filter_name = "ingestion_time_filters" 
    if "query_event_alerts" in filters: 
        ingestion_time_filter_name = "event_ingestion_time_filters"
    # end if

    if filters["key"][0] != "":
        kwargs["keys"] = {"filter": filters["key"][0], "op": filters["key_operator"][0]}
    # end if
    elif "keys" in filters and filters["keys"][0] != "":
        op="notin"
        if not "key_notin_check" in filters:
            op="in"
        # end if
        kwargs["keys"] = {"filter": [], "op": op}
        i = 0
        for key in filters["keys"]:
            kwargs["keys"]["filter"].append(key)
            i+=1
        # end for
    # end if

    if filters["event_value_name"][0] != "":
        value_operators = filters["event_value_operator"]
        value_types = filters["event_value_type"]
        values = filters["event_value"]
        value_name_ops = filters["event_value_name_op"]
        kwargs["value_filters"] = []
        i = 0
        for value_name in filters["event_value_name"]:
            if len(value_name) > 0 and value_name[0] != "":
                if (values[i] == "" and value_types[i] == "text") or (values[i][0] != "" and value_types[i] != "object"):
                    kwargs["value_filters"].append({"name": {"op": value_name_ops[i], "filter": value_name},
                                                          "type": value_types[i],
                                                          "value": {"op": value_operators[i], "filter": values[i]}})
                else:
                    kwargs["value_filters"].append({"name": {"op": value_name_ops[i], "filter": value_name},
                                                          "type": value_types[i]})
            # end if
            i+=1
        # end for
    # end if

    if filters["source"][0] != "":
        op="notlike"
        if not "source_notlike_check" in filters:
            op="like"
        # end if
        kwargs["sources"] = {"filter": filters["source"][0], "op": filters["source_operator"][0]}
    # end if
    elif "sources" in filters and filters["sources"][0] != "":
        op="notin"
        if not "source_notin_check" in filters:
            op="in"
        # end if
        kwargs["sources"] = {"filter": [], "op": op}
        i = 0
        for source in filters["sources"]:
            kwargs["sources"]["filter"].append(source)
            i+=1
        # end for
    # end if
    if filters["er"][0] != "":
        op="notlike"
        if not "er_notlike_check" in filters:
            op="like"
        # end if
        kwargs["explicit_refs"] = {"filter": filters["er"][0], "op": filters["er_operator"][0]}
    # end if
    elif "ers" in filters and filters["ers"][0] != "":
        op="notin"
        if not "er_notin_check" in filters:
            op="in"
        # end if
        kwargs["explicit_refs"] = {"filter": [], "op": op}
        i = 0
        for er in filters["ers"]:
            kwargs["explicit_refs"]["filter"].append(er)
            i+=1
        # end for
    # end if
    if filters["gauge_name"][0] != "":
        op="notlike"
        if not "gauge_name_notlike_check" in filters:
            op="like"
        # end if
        kwargs["gauge_names"] = {"filter": filters["gauge_name"][0], "op": filters["gauge_name_operator"][0]}
    # end if
    elif "gauge_names" in filters and filters["gauge_names"][0] != "":
        op="notin"
        if not "gauge_name_notin_check" in filters:
            op="in"
        # end if
        kwargs["gauge_names"] = {"filter": [], "op": op}
        i = 0
        for gauge_name in filters["gauge_names"]:
            kwargs["gauge_names"]["filter"].append(gauge_name)
            i+=1
        # end for
    # end if
    if filters["gauge_system"][0] != "":
        op="notlike"
        if not "gauge_system_notlike_check" in filters:
            op="like"
        # end if
        kwargs["gauge_systems"] = {"filter": filters["gauge_system"][0], "op": filters["gauge_system_operator"][0]}
    # end if
    elif "gauge_systems" in filters and filters["gauge_systems"][0] != "":
        op="notin"
        if not "gauge_system_notin_check" in filters:
            op="in"
        # end if
        kwargs["gauge_systems"] = {"filter": [], "op": op}
        i = 0
        for gauge_system in filters["gauge_systems"]:
            kwargs["gauge_systems"]["filter"].append(gauge_system)
            i+=1
        # end for
    # end if
    if filters["start"][0] != "":
        kwargs["start_filters"] = []
        i = 0
        operators = filters["start_operator"]
        for start in filters["start"]:
            kwargs["start_filters"].append({"date": start, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["stop"][0] != "":
        kwargs["stop_filters"] = []
        i = 0
        operators = filters["stop_operator"]
        for stop in filters["stop"]:
            kwargs["stop_filters"].append({"date": stop, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["ingestion_time"][0] != "":
        kwargs[ingestion_time_filter_name] = []
        i = 0
        operators = filters["ingestion_time_operator"]
        for ingestion_time in filters["ingestion_time"]:
            kwargs[ingestion_time_filter_name].append({"date": ingestion_time, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["event_duration"][0] != "":
        kwargs["duration_filters"] = []
        i = 0
        operators = filters["event_duration_operator"]
        for event_duration in filters["event_duration"]:
            kwargs["duration_filters"].append({"float": float(event_duration), "op": operators[i]})
            i+=1
        # end for
    # end if

    # Query restrictions
    if filters["order_by"][0] != "":
        descending = True
        if not "order_descending" in filters:
            descending = False
        # end if
        kwargs["order_by"] = {"field": filters["order_by"][0], "descending": descending}
    # end if

    if filters["limit"][0] != "":
        kwargs["limit"] = filters["limit"][0]
    # end if

    if filters["offset"][0] != "":
        kwargs["offset"] = filters["offset"][0]
    # end if

    return kwargs

@bp.route("/query-event-links/<uuid:event_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_event_links_and_render(event_uuid):
    """
    Query events linked to the event corresponding to the UUID received and render.
    """
    current_app.logger.debug("Query event links and render")
    links = query_event_links(event_uuid)
    events = links["prime_events"] + [link["event"] for link in links["events_linking"]] + [link["event"] for link in links["linked_events"]]
    events_geometries = [{"event": event, "geometries": engine.geometries_to_wkt(event.eventGeometries)} for event in events if len(event.eventGeometries) > 0]
    return render_template("eboa_nav/linked_events_nav.html", links=links, events=events, events_geometries=events_geometries)

def query_event_links(event_uuid):
    """
    Query events linked to the event corresponding to the UUID received.
    """
    current_app.logger.debug("Query event links")
    links = query.get_linked_events_details(event_uuid=event_uuid, back_ref = True)

    return links

@bp.route("/query-jsonify-event-values/<uuid:event_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_event_values(event_uuid):
    """
    Query values related to the event with the corresponding received UUID.
    """
    current_app.logger.debug("Query values corresponding to the event with specified UUID " + str(event_uuid))
    values = query.get_event_values([event_uuid])
    jsonified_values = [value.jsonify() for value in values]
    return jsonify(jsonified_values)

@bp.route("/query-annotations", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_annotations_and_render():
    """
    Query annotations and render.
    """
    current_app.logger.debug("Query annotations and render")
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
        filters["offset"] = [""]

        if "query_annotations" in filters:
            annotations = query_annotations(filters)
            show = define_what_to_show_annotations(filters)
            annotations_geometries = []
            if show["map"]:
                annotations_geometries = [{"annotation": annotation, "geometries": engine.geometries_to_wkt(annotation.annotationGeometries)} for annotation in annotations if len(annotation.annotationGeometries) > 0]
            # end if

            return render_template("eboa_nav/annotations_nav.html", annotations=annotations, annotations_geometries=annotations_geometries, show=show, filters=filters)
        else:
            annotation_alerts = query_annotation_alerts(filters)
            return render_template("eboa_nav/annotation_alerts_nav.html", alerts=annotation_alerts, filters=filters)
        # end if

    # end if
    return render_template("eboa_nav/query_annotations.html")

@bp.route("/query-annotations-pages", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_annotations_pages():
    """
    Query annotations using pages and render.
    """
    current_app.logger.debug("Query annotations using pages and render")
    filters = request.json
    annotations = query_annotations(filters)
    
    show = define_what_to_show_annotations(filters)
    annotations_geometries = []
    if show["map"]:
        annotations_geometries = [{"annotation": annotation, "geometries": engine.geometries_to_wkt(annotation.annotationGeometries)} for annotation in annotations if len(annotation.annotationGeometries) > 0]
    # end if

    return render_template("eboa_nav/annotations_nav.html", annotations=annotations, annotations_geometries=annotations_geometries, show=show, filters=filters)

def define_what_to_show_annotations(filters):
    """
    Function to define what to show for annotations
    """
    show = {}
    show["map"]=True
    if not "show_map" in filters:
        show["map"] = False
    # end if

    return show

@bp.route("/query-annotations-by-er/<string:er>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_annotations_by_er(er):
    """
    Query annotations associated to the explicit reference received.
    """
    current_app.logger.debug("Query annotations by explicit reference")
    show = {}
    show["map"]=True
    filters = {}
    filters["offset"] = [""]
    filters["limit"] = ["100"]
    
    annotations = query.get_annotations(explicit_refs={"filter": [er], "op": "in"})

    annotations_geometries = [{"annotation": annotation, "geometries": engine.geometries_to_wkt(annotation.annotationGeometries)} for annotation in annotations if len(annotation.annotationGeometries) > 0]

    return render_template("eboa_nav/annotations_nav.html", annotations=annotations, annotations_geometries=annotations_geometries, show=show, filters=filters)

@bp.route("/query-annotation/<uuid:annotation_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_annotation(annotation_uuid):
    """
    Query annotation corresponding to the UUID received.
    """
    current_app.logger.debug("Query annotation")
    
    show = {}
    show["map"]=True
    filters = {}
    filters["offset"] = [""]
    filters["limit"] = ["100"]

    annotation = query.get_annotations(annotation_uuids={"filter": [annotation_uuid], "op": "in"})

    annotation_geometries = []
    if len(annotation[0].annotationGeometries) > 0: 
        annotation_geometries = [{"annotation": annotation, "geometries": engine.geometries_to_wkt(annotation.annotationGeometries)}]

    return render_template("eboa_nav/annotations_nav.html", annotations=annotation, annotations_geometries=annotation_geometries, show=show, filters=filters)

@bp.route("/query-annotations-by-source-uuid/<string:source_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_annotations_by_source_uuid(source_uuid):
    """
    Query annotations associated to the source corresponding to the UUID received.
    """
    current_app.logger.debug("Query annotations by source uuid")
    show = {}
    show["map"]=True
    filters = {}
    filters["offset"] = [""]
    filters["limit"] = ["100"]

    annotations = query.get_annotations(source_uuids={"filter": [source_uuid], "op": "in"})

    annotations_geometries = []
    annotations_geometries = [{"annotation": annotation, "geometries": engine.geometries_to_wkt(annotation.annotationGeometries)} for annotation in annotations if len(annotation.annotationGeometries) > 0]

    return render_template("eboa_nav/annotations_nav.html", annotations=annotations, annotations_geometries=annotations_geometries, show=show, filters=filters)

def query_annotations(filters):
    """
    Query annotations.
    """
    current_app.logger.debug("Query annotations")

    kwargs = set_filters_for_query_annotations_or_annotation_alerts(filters)

    annotations = query.get_annotations(**kwargs)

    return annotations

def query_annotation_alerts(filters):
    """
    Query annotation alerts.
    """
    current_app.logger.debug("Query annotation alerts")

    annotation_kwargs = set_filters_for_query_annotations_or_annotation_alerts(filters)

    alert_kwargs = set_specific_alert_filters(filters)

    kwargs = {**annotation_kwargs, **alert_kwargs}

    annotation_alerts = query.get_annotation_alerts(**kwargs)

    return annotation_alerts

def set_filters_for_query_annotations_or_annotation_alerts(filters):
    """
    Set filter for query annotations or query annotation alerts.
    """
    kwargs = {}

    # Wether is query annotation or query alert annotations
    ingestion_time_filter_name = "ingestion_time_filters"
    if "query_annotation_alerts" in filters: 
        ingestion_time_filter_name = "annotation_ingestion_time_filters"
    # end if
    
    if filters["annotation_value_name"][0] != "":
        value_operators = filters["annotation_value_operator"]
        value_types = filters["annotation_value_type"]
        values = filters["annotation_value"]
        value_name_ops = filters["annotation_value_name_op"]
        kwargs["value_filters"] = []
        i = 0
        for value_name in filters["annotation_value_name"]:
            if len(value_name) > 0 and value_name[0] != "":
                if (values[i] == "" and value_types[i] == "text") or (values[i][0] != "" and value_types[i] != "object"):
                    kwargs["value_filters"].append({"name": {"op": value_name_ops[i], "filter": value_name},
                                                          "type": value_types[i],
                                                          "value": {"op": value_operators[i], "filter": values[i]}})
                else:
                    kwargs["value_filters"].append({"name": {"op": value_name_ops[i], "filter": value_name},
                                                          "type": value_types[i]})
            # end if
            i+=1
        # end for
    # end if

    if filters["source"][0] != "":
        op="notlike"
        if not "source_notlike_check" in filters:
            op="like"
        # end if
        kwargs["sources"] = {"filter": filters["source"][0], "op": filters["source_operator"][0]}
    # end if
    elif "sources" in filters and filters["sources"][0] != "":
        op="notin"
        if not "source_notin_check" in filters:
            op="in"
        # end if
        kwargs["sources"] = {"filter": [], "op": op}
        i = 0
        for source in filters["sources"]:
            kwargs["sources"]["filter"].append(source)
            i+=1
        # end for
    # end if
    if filters["er"][0] != "":
        op="notlike"
        if not "er_notlike_check" in filters:
            op="like"
        # end if
        kwargs["explicit_refs"] = {"filter": filters["er"][0], "op": filters["er_operator"][0]}
    # end if
    elif "ers" in filters and filters["ers"][0] != "":
        op="notin"
        if not "er_notin_check" in filters:
            op="in"
        # end if
        kwargs["explicit_refs"] = {"filter": [], "op": op}
        i = 0
        for er in filters["ers"]:
            kwargs["explicit_refs"]["filter"].append(er)
            i+=1
        # end for
    # end if
    if filters["annotation_name"][0] != "":
        op="notlike"
        if not "annotation_name_notlike_check" in filters:
            op="like"
        # end if
        kwargs["annotation_cnf_names"] = {"filter": filters["annotation_name"][0], "op": filters["annotation_name_operator"][0]}
    # end if
    elif "annotation_names" in filters and filters["annotation_names"][0] != "":
        op="notin"
        if not "annotation_name_notin_check" in filters:
            op="in"
        # end if
        kwargs["annotation_cnf_names"] = {"filter": [], "op": op}
        i = 0
        for annotation_name in filters["annotation_names"]:
            kwargs["annotation_cnf_names"]["filter"].append(annotation_name)
            i+=1
        # end for
    # end if
    if filters["annotation_system"][0] != "":
        op="notlike"
        if not "annotation_system_notlike_check" in filters:
            op="like"
        # end if
        kwargs["annotation_cnf_systems"] = {"filter": filters["annotation_system"][0], "op": filters["annotation_system_operator"][0]}
    # end if
    elif "annotation_systems" in filters and filters["annotation_systems"][0] != "":
        op="notin"
        if not "annotation_system_notin_check" in filters:
            op="in"
        # end if
        kwargs["annotation_cnf_systems"] = {"filter": [], "op": op}
        i = 0
        for annotation_system in filters["annotation_systems"]:
            kwargs["annotation_cnf_systems"]["filter"].append(annotation_system)
            i+=1
        # end for
    # end if
    if filters["ingestion_time"][0] != "":
        kwargs[ingestion_time_filter_name] = []
        i = 0
        operators = filters["ingestion_time_operator"]
        for ingestion_time in filters["ingestion_time"]:
            kwargs[ingestion_time_filter_name].append({"date": ingestion_time, "op": operators[i]})
            i+=1
        # end for
    # end if

    # Query restrictions
    if filters["order_by"][0] != "":
        descending = True
        if not "order_descending" in filters:
            descending = False
        # end if
        kwargs["order_by"] = {"field": filters["order_by"][0], "descending": descending}
    # end if

    if filters["limit"][0] != "":
        kwargs["limit"] = filters["limit"][0]
    # end if

    if filters["offset"][0] != "":
        kwargs["offset"] = filters["offset"][0]
    # end if

    return kwargs

@bp.route("/query-jsonify-annotation-values/<uuid:annotation_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_annotation_values(annotation_uuid):
    """
    Query values related to the annotation with the corresponding received UUID.
    """
    current_app.logger.debug("Query values corresponding to the annotation with specified UUID " + str(annotation_uuid))
    values = query.get_annotation_values([annotation_uuid])
    jsonified_values = [value.jsonify() for value in values]
    return jsonify(jsonified_values)

@bp.route("/query-sources", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_sources_and_render():
    """
    Query sources amd render.
    """
    current_app.logger.debug("Query sources and render")
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
        filters["offset"] = [""]

        if "query_sources" in filters:
            sources = query_sources(filters)
            show = define_what_to_show_sources(filters)
            return render_template("eboa_nav/sources_nav.html", sources=sources, show=show, filters=filters)
        else:
            source_alerts = query_source_alerts(filters)
            return render_template("eboa_nav/source_alerts_nav.html", alerts=source_alerts, filters=filters)
        # end if
    # end if

    return render_template("eboa_nav/query_sources.html")

@bp.route("/query-sources-pages", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_sources_pages():
    """
    Query sources using pages and render.
    """
    current_app.logger.debug("Query sources using pages and render")
    filters = request.json

    sources = query_sources(filters)
    show = define_what_to_show_sources(filters)
    return render_template("eboa_nav/sources_nav.html", sources=sources, show=show, filters=filters)

def define_what_to_show_sources(filters):
    """
    Function to define what to show for sources
    """

    show = {}
    show["validity_timeline"]=True
    if not "show_validity_timeline" in filters:
        show["validity_timeline"] = False
    # end if
    show["generation_to_ingestion_timeline"]=True
    if not "show_generation_to_ingestion_timeline" in filters:
        show["generation_to_ingestion_timeline"] = False
    # end if
    show["number_events_xy"]=True
    if not "show_number_events_xy" in filters:
        show["number_events_xy"] = False
    # end if
    show["ingestion_duration_xy"]=True
    if not "show_ingestion_duration_xy" in filters:
        show["ingestion_duration_xy"] = False
    # end if
    show["generation_time_to_ingestion_time_xy"]=True
    if not "show_generation_time_to_ingestion_time_xy" in filters:
        show["generation_time_to_ingestion_time_xy"] = False
    # end if
    
    return show

def query_sources(filters):
    """
    Query sources.
    """
    current_app.logger.debug("Query sources")
    
    kwargs = set_filters_for_query_sources_or_source_alerts(filters)

    sources = query.get_sources(**kwargs)

    return sources

def query_source_alerts(filters):
    """
    Query source alerts.
    """
    current_app.logger.debug("Query source alerts")

    source_kwargs = set_filters_for_query_sources_or_source_alerts(filters)

    alert_kwargs = set_specific_alert_filters(filters)

    kwargs = {**source_kwargs, **alert_kwargs}

    source_alerts = query.get_source_alerts(**kwargs)

    return source_alerts

def set_filters_for_query_sources_or_source_alerts(filters):
    """
    Set filter for query sources or query source alerts.
    """
    kwargs = {}
    
    # Wether is query source or query source alerts
    ingestion_time_filter_name = "ingestion_time_filters" 
    source_filter_name = "names"
    if "query_source_alerts" in filters: 
        ingestion_time_filter_name = "source_ingestion_time_filters"
        source_filter_name = "source_names"
    # end if
    
    if filters["source"][0] != "":
        op="notlike"
        if not "source_notlike_check" in filters:
            op="like"
        # end if
        kwargs[source_filter_name] = {"filter": filters["source"][0], "op": filters["source_operator"][0]}
    # end if
    elif "sources" in filters and filters["sources"][0] != "":
        op="notin"
        if not "source_notin_check" in filters:
            op="in"
        # end if
        kwargs[source_filter_name] = {"filter": [], "op": op}
        i = 0
        for source in filters["sources"]:
            kwargs[source_filter_name]["filter"].append(source)
            i+=1
        # end for
    # end if
    if filters["dim_signature"][0] != "":
        op="notlike"
        if not "dim_signature_notlike_check" in filters:
            op="like"
        # end if
        kwargs["dim_signatures"] = {"filter": filters["dim_signature"][0], "op": filters["dim_signature_operator"][0]}
    # end if
    elif "dim_signatures" in filters and filters["dim_signatures"][0] != "":
        op="notin"
        if not "dim_signature_notin_check" in filters:
            op="in"
        # end if
        kwargs["dim_signatures"] = {"filter": [], "op": op}
        i = 0
        for dim_signature in filters["dim_signatures"]:
            kwargs["dim_signatures"]["filter"].append(dim_signature)
            i+=1
        # end for
    # end if
    if filters["validity_start"][0] != "":
        kwargs["validity_start_filters"] = []
        i = 0
        operators = filters["validity_start_operator"]
        for start in filters["validity_start"]:
            kwargs["validity_start_filters"].append({"date": start, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["validity_stop"][0] != "":
        kwargs["validity_stop_filters"] = []
        i = 0
        operators = filters["validity_stop_operator"]
        for stop in filters["validity_stop"]:
            kwargs["validity_stop_filters"].append({"date": stop, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["reported_validity_start"][0] != "":
        kwargs["reported_validity_start_filters"] = []
        i = 0
        operators = filters["reported_validity_start_operator"]
        for start in filters["reported_validity_start"]:
            kwargs["reported_validity_start_filters"].append({"date": start, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["reported_validity_stop"][0] != "":
        kwargs["reported_validity_stop_filters"] = []
        i = 0
        operators = filters["reported_validity_stop_operator"]
        for stop in filters["reported_validity_stop"]:
            kwargs["reported_validity_stop_filters"].append({"date": stop, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["reception_time"][0] != "":
        kwargs["reception_time_filters"] = []
        i = 0
        operators = filters["reception_time_operator"]
        for reception_time in filters["reception_time"]:
            kwargs["reception_time_filters"].append({"date": reception_time, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["ingestion_time"][0] != "":
        kwargs[ingestion_time_filter_name] = []
        i = 0
        operators = filters["ingestion_time_operator"]
        for ingestion_time in filters["ingestion_time"]:
            kwargs[ingestion_time_filter_name].append({"date": ingestion_time, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["processing_duration"][0] != "":
        kwargs["processing_duration_filters"] = []
        i = 0
        operators = filters["processing_duration_operator"]
        for processing_duration in filters["processing_duration"]:
            kwargs["processing_duration_filters"].append({"float": float(processing_duration), "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["ingestion_duration"][0] != "":
        kwargs["ingestion_duration_filters"] = []
        i = 0
        operators = filters["ingestion_duration_operator"]
        for ingestion_duration in filters["ingestion_duration"]:
            kwargs["ingestion_duration_filters"].append({"float": float(ingestion_duration), "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["generation_time"][0] != "":
        kwargs["generation_time_filters"] = []
        i = 0
        operators = filters["generation_time_operator"]
        for generation_time in filters["generation_time"]:
            kwargs["generation_time_filters"].append({"date": generation_time, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["reported_generation_time"][0] != "":
        kwargs["reported_generation_time_filters"] = []
        i = 0
        operators = filters["reported_generation_time_operator"]
        for reported_generation_time in filters["reported_generation_time"]:
            kwargs["reported_generation_time_filters"].append({"date": reported_generation_time, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["ingestion_completeness"][0] != "":
        kwargs["ingestion_completeness"] = bool(util.strtobool(filters["ingestion_completeness"][0]))
    # end if
    if filters["processor"][0] != "":
        op="notlike"
        if not "processor_notlike_check" in filters:
            op="like"
        # end if
        kwargs["processors"] = {"filter": filters["processor"][0], "op": filters["processor_operator"][0]}
    # end if
    elif "processors" in filters and filters["processors"][0] != "":
        op="notin"
        if not "processor_notin_check" in filters:
            op="in"
        # end if
        kwargs["processors"] = {"filter": [], "op": op}
        i = 0
        for processor in filters["processors"]:
            kwargs["processors"]["filter"].append(processor)
            i+=1
        # end for
    # end if

    if filters["source_validity_duration"][0] != "":
        kwargs["validity_duration_filters"] = []
        i = 0
        operators = filters["source_validity_duration_operator"]
        for source_validity_duration in filters["source_validity_duration"]:
            kwargs["validity_duration_filters"].append({"float": float(source_validity_duration), "op": operators[i]})
            i+=1
        # end for
    # end if

    if "source_statuses" in filters and filters["source_statuses"][0] != "":
        op="notin"
        if not "status_notin_check" in filters:
            op="in"
        # end if
        kwargs["statuses"] = {"filter": [], "op": op}
        i = 0
        for status in filters["source_statuses"]:
            kwargs["statuses"]["filter"].append(str(eboa_engine.exit_codes[status]["status"]))
            i+=1
        # end for
    # end if
    
    # Query restrictions
    if filters["order_by"][0] != "":
        descending = True
        if not "order_descending" in filters:
            descending = False
        # end if
        kwargs["order_by"] = {"field": filters["order_by"][0], "descending": descending}
    # end if

    if filters["limit"][0] != "":
        kwargs["limit"] = filters["limit"][0]
    # end if

    if filters["offset"][0] != "":
        kwargs["offset"] = filters["offset"][0]
    # end if

    return kwargs

@bp.route("/query-source/<uuid:source_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_source(source_uuid):
    """
    Query source corresponding to the UUID received.
    """
    current_app.logger.debug("Query source")
    source = query.get_sources(source_uuids={"filter": [source_uuid], "op": "in"})
    show = {}
    show["validity_timeline"]=True
    show["generation_to_ingestion_timeline"]=True
    show["number_events_xy"]=True
    show["ingestion_duration_xy"]=True
    show["generation_time_to_ingestion_time_xy"]=True

    filters = {}
    filters["offset"] = [""]
    filters["limit"] = ["100"]
    
    return render_template("eboa_nav/sources_nav.html", sources=source, show=show, filters=filters)

@bp.route("/query-sources-by-name/<string:name>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_sources_by_name(name):
    """
    Query sources corresponding to the name received.
    """
    current_app.logger.debug("Query sources by name")
    sources = query.get_sources(names={"filter": name, "op": "=="})
    show = {}
    show["validity_timeline"]=True
    show["generation_to_ingestion_timeline"]=True
    show["number_events_xy"]=True
    show["ingestion_duration_xy"]=True
    show["generation_time_to_ingestion_time_xy"]=True

    filters = {}
    filters["offset"] = [""]
    filters["limit"] = ["100"]
    
    return render_template("eboa_nav/sources_nav.html", sources=sources, show=show, filters=filters)

@bp.route("/query-sources-by-dim/<uuid:dim_signature_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_sources_by_dim(dim_signature_uuid):
    """
    Query sources associated to the DIM signature corresponding to the UUID received.
    """
    current_app.logger.debug("Query sources by DIM signature")
    sources = query.get_sources(dim_signature_uuids={"filter": [dim_signature_uuid], "op": "in"})
    show = {}
    show["validity_timeline"]=True
    show["generation_to_ingestion_timeline"]=True
    show["number_events_xy"]=True
    show["ingestion_duration_xy"]=True
    show["generation_time_to_ingestion_time_xy"]=True

    filters = {}    
    filters["offset"] = [""]
    filters["limit"] = ["100"]
    
    return render_template("eboa_nav/sources_nav.html", sources=sources, show=show, filters=filters)

@bp.route("/query-jsonify-sources")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_sources():
    """
    Query all the sources.
    """

    current_app.logger.debug("Query source")

    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["order_by"] = {"field": "reception_time", "descending": True}
    kwargs["names"] = {"filter": search, "op": "=="}

    sources = query.get_sources(**kwargs)
    jsonified_sources = [source.jsonify() for source in sources]
    return jsonify(jsonified_sources)

@bp.route("/query-jsonify-sources-by-processor")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_sources_by_processor():
    """
    Query all the sources.
    """

    current_app.logger.debug("Query source")

    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["order_by"] = {"field": "reception_time", "descending": True}
    kwargs["processors"] = {"filter": "%" + search + "%", "op": "like"}

    sources = query.get_sources(**kwargs)
    jsonified_sources = [source.jsonify() for source in sources]
    return jsonify(jsonified_sources)

@bp.route("/query-jsonify-source-statuses/<uuid:source_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_source_statuses(source_uuid):
    """
    Query statuses related to the source with the corresponding received UUID.
    """
    current_app.logger.debug("Query statuses corresponding to the source with the specified UUID " + str(source_uuid))
    sources = query.get_sources(source_uuids = {"filter": [source_uuid], "op": "in"})
    jsonified_statuses = [source_status.jsonify() for source in sources for source_status in source.statuses]
    return jsonify(jsonified_statuses)

@bp.route("/get-source-status")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def get_source_status():
    """
    Get the source statuses defined in the EBOA component.
    """
    current_app.logger.debug("Get source statuses")
    return jsonify(eboa_engine.exit_codes)

def prepare_reingestion_of_sources_and_dependencies(sources, source_uuids_matching_triggering_rule, source_uuids_not_matching_triggering_rule):

    sources_to_follow_reingestion = []
    
    if len(sources) > 0:
        # Get triggering configuration
        triggering_xpath = get_triggering_conf()
        for source in sources:
            matching_rules = triggering_xpath("/triggering_rules/rule[match(source_mask, $file_name)]", file_name = source.name)
            if len(matching_rules) > 0:
                rule = matching_rules[0]
                skip = rule.get("skip")
                if skip != "true":
                    source_uuids_matching_triggering_rule.append(source.source_uuid)
                    source_type = triggering_xpath("/triggering_rules/rule[match(source_mask, $file_name)]/source_type", file_name = source.name)[0].text
                    source_masks_depending_on_this = triggering_xpath("/triggering_rules/rule[dependencies/source_type = $source_type]/source_mask", source_type = source_type)
                    if len(source_masks_depending_on_this) > 0:
                        source_masks_sql = [source_mask.text.replace('.*', '%').replace('.', '_').replace('*', '%') for source_mask in source_masks_depending_on_this]
                        # Obtain events linking to the events of the source
                        event_uuid_links = [link.event_uuid_link for event in source.events for link in event.eventLinks]

                        for source_mask_sql in source_masks_sql:
                            events = query.get_events(event_uuids = {"filter": event_uuid_links, "op": "in"}, sources = {"filter": source_mask_sql, "op": "like"})
                            sources_linked = [event.source for event in events]
                            sources_to_follow_reingestion = sources_to_follow_reingestion + [source for source in sources_linked if source.source_uuid not in source_uuids_matching_triggering_rule]
                        # end for
                    # end if
                else:
                    source_uuids_not_matching_triggering_rule.append(source.source_uuid)
                # end if
            else:
                source_uuids_not_matching_triggering_rule.append(source.source_uuid)
            # end if
        # end for
    # end if

    if len(sources_to_follow_reingestion) > 0:
        prepare_reingestion_of_sources_and_dependencies(list(set(sources_to_follow_reingestion)), source_uuids_matching_triggering_rule, source_uuids_not_matching_triggering_rule)
    # end if

    return

@bp.route("/prepare-reingestion-of-sources", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator")
def prepare_reingestion_of_sources():
    """
    Prepare reingestion of selected sources.
    """
    current_app.logger.debug("Prepare reingestion of selected sources")
    filters = request.json
    sources_from_uuids = query.get_sources(source_uuids = {"filter": filters["sources"], "op": "in"})

    sources = query.get_sources(names = {"filter": [source.name for source in sources_from_uuids], "op": "in"})

    source_uuids_matching_triggering_rule = []
    source_uuids_not_matching_triggering_rule = []
    prepare_reingestion_of_sources_and_dependencies(sources, source_uuids_matching_triggering_rule, source_uuids_not_matching_triggering_rule)

    sources_matching_triggering_rule = query.get_sources(source_uuids = {"filter": source_uuids_matching_triggering_rule, "op": "in"})

    sources_not_matching_triggering_rule = query.get_sources(source_uuids = {"filter": source_uuids_not_matching_triggering_rule, "op": "in"})

    return render_template("eboa_nav/reingestion_of_sources.html", sources_matching_triggering_rule=sources_matching_triggering_rule, sources_not_matching_triggering_rule=sources_not_matching_triggering_rule)

@bp.route("/reingest-sources", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator")
def reingest_sources():
    """
    Re-ingest selected sources.
    """
    current_app.logger.debug("Re-ingest selected sources")
    filters = request.json

    sources_to_reingest = set(filters["sources"])
    
    # Create temporal folder inside /inputs folder to copy sources there for ORC to re-ingest
    temporal_folder = tempfile.TemporaryDirectory(prefix = ".", dir="/inputs/")
    
    # Get metadata of sources
    sources_metadata = {}
    for source_name in sources_to_reingest:
        # Get source metadata from minArc
        sources_metadata[source_name] = _get_metadata_source(source_name)

        if "filename" not in sources_metadata[source_name] or "path" not in sources_metadata[source_name]:
            return {"status": "NOK",
                    "error": f"Source with name {source_name} is not available in the archive"}
        # end if
    # end for

    # Copy sources to temporal folder and delete from ORC
    for source_name in sources_to_reingest:

        # Retrieve file from the archive
        if sources_metadata[source_name]["remote_archive"]:
            command = "minArcRetrieve --Location " + temporal_folder.name + " --Unpack --file " + source_name
            command_split = shlex.split(command)
            program = Popen(command_split, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            output, error = program.communicate()        
            return_code = program.returncode
        else:
            command = "minArcRetrieve --noserver --Location " + temporal_folder.name + " --Unpack --file " + source_name
            command_split = shlex.split(command)
            program = Popen(command_split, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            output, error = program.communicate()        
            return_code = program.returncode
        # end if

        if error:
            return {"status": "NOK",
                    "error": f"Source with name {source_name} could not be retrieved from minArc. minArc gave the following output: {output} and the following error: {error}"}
        # end if

        # Delete source from ORC
        command = "orcQueueInput -d " + source_name
        command_split = shlex.split(command)
        program = Popen(command_split, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, error = program.communicate()        
        return_code = program.returncode

        if error:
            return {"status": "NOK",
                    "error": f"Source with name {source_name} could not be removed inside ORC. ORC gave the following output: {output} and the following error: {error}"}
        # end if

    # end for

    # Delete sources from BOA
    query.get_sources(names = {"filter": list(sources_to_reingest), "op": "in"}, delete=True)

    # Move sources to /inputs
    for source_name in sources_to_reingest:
        # Copy source to temporal folder
        shutil.move(temporal_folder.name + "/" + source_name, "/inputs")
    # end for

    # Delete temporal folder
    temporal_folder.cleanup()

    return {"status": "OK"}

@bp.route("/prepare-deletion-of-sources", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator")
def prepare_deletion_of_sources():
    """
    Prepare deletion of selected sources.
    """
    current_app.logger.debug("Prepare deletion of selected sources")
    filters = request.json
    sources_from_uuids = query.get_sources(source_uuids = {"filter": filters["sources"], "op": "in"})

    sources = query.get_sources(names = {"filter": [source.name for source in sources_from_uuids], "op": "in"})

    return render_template("eboa_nav/deletion_of_sources.html", sources=sources)

def _get_metadata_source(source_name):
    """
    Get metadata of the specified source.
    :param source_name: string with the source name to get the associated metadata
    :type source_name: str

    :return: Dictionary with metadata
    :rtype: dict
    """

    command = "minArcStatus --file " + source_name
    command_split = shlex.split(command)
    program = Popen(command_split, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, error = program.communicate()        
    return_code = program.returncode
    remote_archive = True
    
    output_json = {}
    
    # If remote minArc server does not give answer, try with the local server
    if output.decode() == "":
        command = "minArcStatus --noserver --file " + source_name
        command_split = shlex.split(command)
        program = Popen(command_split, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, error = program.communicate()        
        return_code = program.returncode
        remote_archive = False
    # end if

    if output.decode() != "":
        # Get metadata from minArcStatus output
        output_json = json.loads(output.decode())
    # end if

    output_json["remote_archive"] = remote_archive

    return output_json

@bp.route("/download-source/<string:source_name>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def download_source(source_name):
    """
    Download of selected source.
    """
    current_app.logger.debug("Download of selected source")

    output_json = _get_metadata_source(source_name)
    filename = ""
    filepath = ""

    if "filename" in output_json and "path" in output_json:
        # Get filename and filepath from minArcStatus output
        filename = output_json["filename"]
        filepath = output_json["path"]
    # end if
    
    return send_from_directory(filepath, filename, as_attachment=True)

@bp.route("/delete-sources", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator")
def delete_sources():
    """
    Delete selected sources.
    """
    current_app.logger.debug("Delete selected sources")
    filters = request.json
    query.get_sources(names = {"filter": filters["sources"], "op": "in"}, delete=True)

    return {"status": "OK"}

@bp.route("/query-gauges", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_gauges_and_render():
    """
    Query gauges amd render.
    """
    current_app.logger.debug("Query gauges and render")
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
        filters["offset"] = [""]
        gauges = query_gauges(filters)

        show = define_what_to_show_gauges(filters)

        links = []
        if show["network"]:
            links = query_linked_gauges(gauges)
        # end if
        
        return render_template("eboa_nav/gauges_nav.html", gauges=gauges, links=links, show=show, filters=filters)
    # end if

    return render_template("eboa_nav/query_gauges.html")

@bp.route("/query-gauges-pages", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_gauges_pages():
    """
    Query gauges using pages and render.
    """
    current_app.logger.debug("Query gauges using pages and render")

    filters = request.json
    gauges = query_gauges(filters)

    show = define_what_to_show_gauges(filters)

    links = []
    if show["network"]:
        links = query_linked_gauges(gauges)
    # end if

    return render_template("eboa_nav/gauges_nav.html", gauges=gauges, links=links, show=show, filters=filters)

def define_what_to_show_gauges(filters):

    show = {}
    if not "show_network" in filters:
        show["network"] = False
    else:
        show["network"]=True
    # end if

    return show
    
@bp.route("/query-gauges-by-dim/<uuid:dim_signature_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_gauges_by_dim(dim_signature_uuid):
    """
    Query gauges associated to the DIM signature corresponding to the UUID received.
    """
    current_app.logger.debug("Query gauges by DIM signature")
    gauges = query.get_gauges(dim_signature_uuids={"filter": [dim_signature_uuid], "op": "in"})
    show = {}
    show["network"]=True

    filters = {}
    filters["offset"] = [""]
    filters["limit"] = ["100"]
    
    links = query_linked_gauges(gauges)

    return render_template("eboa_nav/gauges_nav.html", gauges=gauges, links=links, show=show, filters=filters)

def register_gauge_node (links, gauge, registered_gauges):
    """
    Register gauge node for the linked gauges.
    """
    if gauge.gauge_uuid not in registered_gauges:
        registered_gauges[gauge.gauge_uuid] = {
            "gauge_uuid": str(gauge.gauge_uuid),
            "name": gauge.name,
            "system": gauge.system,
            "dim_signature_uuid": gauge.dim_signature_uuid,
            "dim_signature_name": gauge.dim_signature.dim_signature,
            "gauges_linking": [],
            "gauges_linked": []
        }
        links.append(registered_gauges[gauge.gauge_uuid])
    # end if
    return registered_gauges[gauge.gauge_uuid]

def query_linked_gauges(gauges):
    """
    Query linked gauges.
    """
    current_app.logger.debug("Query linked gauges")
    links = []
    linked_gauges = {}
    registered_gauges = {}
    for gauge in gauges:
        gauge_node = register_gauge_node(links, gauge, registered_gauges)
        # Get the associated events
        events = query.get_events(gauge_uuids = {"filter": [gauge.gauge_uuid], "op": "in"},
                                  limit = 1)
        if len(events) > 0:
            # Get the events that link to the related events
            linking_event_uuids = [event_link.event_uuid_link for event_link in events[0].eventLinks]
            linking_events = query.get_events(event_uuids = {"filter": linking_event_uuids, "op": "in"})

            # Get the events that linked by the related events
            linked_event_links = query.get_event_links(event_uuid_links = {"filter": [events[0].event_uuid], "op": "in"})
            linked_event_uuids = [event_link.event_uuid for event_link in linked_event_links]
            linked_events = query.get_events(event_uuids = {"filter": linked_event_uuids, "op": "in"})

            # Get the gauges associated to the events linking to the related events
            gauges_linking = set([(str(event.gauge.gauge_uuid), [event_link.name for event_link in events[0].eventLinks if event_link.event_uuid_link == event.event_uuid][0]) for event in linking_events])

            # Get the gauges associated to the events linked by the related events
            gauges_linked = set([(str(event.gauge.gauge_uuid), [event_link.name for event_link in linked_event_links if event_link.event_uuid == event.event_uuid][0]) for event in linked_events])

            linking_linked_events = set (linked_events + linking_events)
            unique_linking_linked_gauges = set([event.gauge for event in linking_linked_events])
            for linking_linked_gauge in unique_linking_linked_gauges:
                register_gauge_node(links, linking_linked_gauge, registered_gauges)
            # end for
            
            # Associate gauges
            for gauge_linking in gauges_linking:
                gauge_linking_uuid = gauge_linking[0]
                link_name = gauge_linking[1]
                if (gauge_linking_uuid, str(gauge.gauge_uuid)) not in linked_gauges:
                    linked_gauges[(gauge_linking_uuid, str(gauge.gauge_uuid))] = True
                    gauge_node["gauges_linking"].append({"gauge_uuid": gauge_linking_uuid, "link_name": link_name})
                # end if
            # end for
            for gauge_linked in gauges_linked:
                gauge_linked_uuid = gauge_linked[0]
                link_name = gauge_linked[1]
                if (str(gauge.gauge_uuid), gauge_linked_uuid) not in linked_gauges:
                    linked_gauges[(str(gauge.gauge_uuid), gauge_linked_uuid)] = True
                    gauge_node["gauges_linked"].append({"gauge_uuid": gauge_linked_uuid, "link_name": link_name})
                # end if
            # end for
        # end if
    # end for

    return links

def query_gauges(filters):
    """
    Query gauges.
    """
    current_app.logger.debug("Query gauges")
    kwargs = {}
    if filters["gauge_name"][0] != "":
        op="notlike"
        if not "gauge_name_notlike_check" in filters:
            op="like"
        # end if
        kwargs["names"] = {"filter": filters["gauge_name"][0], "op": filters["gauge_name_operator"][0]}
    # end if
    elif "gauge_names" in filters and filters["gauge_names"][0] != "":
        op="notin"
        if not "gauge_name_notin_check" in filters:
            op="in"
        # end if
        kwargs["names"] = {"filter": [], "op": op}
        i = 0
        for gauge_name in filters["gauge_names"]:
            kwargs["names"]["filter"].append(gauge_name)
            i+=1
        # end for
    # end if
    if filters["gauge_system"][0] != "":
        op="notlike"
        if not "gauge_system_notlike_check" in filters:
            op="like"
        # end if
        kwargs["systems"] = {"filter": filters["gauge_system"][0], "op": filters["gauge_system_operator"][0]}
    # end if
    elif "gauge_systems" in filters and filters["gauge_systems"][0] != "":
        op="notin"
        if not "gauge_system_notin_check" in filters:
            op="in"
        # end if
        kwargs["systems"] = {"filter": [], "op": op}
        i = 0
        for gauge_system in filters["gauge_systems"]:
            kwargs["systems"]["filter"].append(gauge_system)
            i+=1
        # end for
    # end if
    if filters["dim_signature"][0] != "":
        op="notlike"
        if not "dim_signature_notlike_check" in filters:
            op="like"
        # end if
        kwargs["dim_signatures"] = {"filter": filters["dim_signature"][0], "op": filters["dim_signature_operator"][0]}
    # end if
    elif "dim_signatures" in filters and filters["dim_signatures"][0] != "":
        op="notin"
        if not "dim_signature_notin_check" in filters:
            op="in"
        # end if
        kwargs["dim_signatures"] = {"filter": [], "op": op}
        i = 0
        for dim_signature in filters["dim_signatures"]:
            kwargs["dim_signatures"]["filter"].append(dim_signature)
            i+=1
        # end for
    # end if

    # Query restrictions
    if filters["order_by"][0] != "":
        descending = True
        if not "order_descending" in filters:
            descending = False
        # end if
        kwargs["order_by"] = {"field": filters["order_by"][0], "descending": descending}
    # end if

    if filters["limit"][0] != "":
        kwargs["limit"] = filters["limit"][0]
    # end if

    if filters["offset"][0] != "":
        kwargs["offset"] = filters["offset"][0]
    # end if

    gauges = query.get_gauges(**kwargs)

    return gauges

@bp.route("/query-jsonify-gauges-by-name")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_gauges_by_name():
    """
    Query all the gauges.
    """
    current_app.logger.debug("Query gauge by name")
    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["names"] = {"filter": "%" + search + "%", "op": "like"}

    gauges = query.get_gauges(**kwargs)
    jsonified_gauges = [gauge.jsonify() for gauge in gauges]
    return jsonify(jsonified_gauges)

@bp.route("/query-jsonify-gauges-by-system")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_gauges_by_system():
    """
    Query all the gauges.
    """
    current_app.logger.debug("Query gauge by system")
    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["systems"] = {"filter": "%" + search + "%", "op": "like"}

    gauges = query.get_gauges(**kwargs)
    jsonified_gauges = [gauge.jsonify() for gauge in gauges]
    return jsonify(jsonified_gauges)

@bp.route("/query-annotation-cnfs", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_annotation_cnfs_and_render():
    """
    Query annotation configurations amd render.
    """
    current_app.logger.debug("Query annotation configurations and render")
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
        filters["offset"] = [""]
        annotation_cnfs = query_annotation_cnfs(filters)

        return render_template("eboa_nav/annotation_cnfs_nav.html", annotation_cnfs=annotation_cnfs, filters=filters)
    # end if

    return render_template("eboa_nav/query_annotation_cnfs.html")

@bp.route("/query-annotation-cnfs-pages", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_annotation_cnfs_pages():
    """
    Query annotation configurations using pages and render.
    """
    current_app.logger.debug("Query annotation configurations using pages and render")
    filters = request.json
    annotation_cnfs = query_annotation_cnfs(filters)

    return render_template("eboa_nav/annotation_cnfs_nav.html", annotation_cnfs=annotation_cnfs, filters=filters)

@bp.route("/query-annotation-cnfs-by-dim/<uuid:dim_signature_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_annotation_cnfs_by_dim(dim_signature_uuid):
    """
    Query annotation configurations associated to the DIM signature corresponding to the UUID received.
    """
    current_app.logger.debug("Query annotation configurations by DIM signature")
    annotation_cnfs = query.get_annotation_cnfs(dim_signature_uuids={"filter": [dim_signature_uuid], "op": "in"})

    filters = {}
    filters["offset"] = [""]
    filters["limit"] = ["100"]
    
    return render_template("eboa_nav/annotation_cnfs_nav.html", annotation_cnfs=annotation_cnfs, filters=filters)

def query_annotation_cnfs(filters):
    """
    Query annotation configurations.
    """
    current_app.logger.debug("Query annotation configurations")
    kwargs = {}
    if filters["annotation_name"][0] != "":
        op="notlike"
        if not "annotation_name_notlike_check" in filters:
            op="like"
        # end if
        kwargs["names"] = {"filter": filters["annotation_name"][0], "op": filters["annotation_name_operator"][0]}
    # end if
    elif "annotation_names" in filters and filters["annotation_names"][0] != "":
        op="notin"
        if not "annotation_name_notin_check" in filters:
            op="in"
        # end if
        kwargs["names"] = {"filter": [], "op": op}
        i = 0
        for annotation_name in filters["annotation_names"]:
            kwargs["names"]["filter"].append(annotation_name)
            i+=1
        # end for
    # end if
    if filters["annotation_system"][0] != "":
        op="notlike"
        if not "annotation_system_notlike_check" in filters:
            op="like"
        # end if
        kwargs["systems"] = {"filter": filters["annotation_system"][0], "op": filters["annotation_system_operator"][0]}
    # end if
    elif "annotation_systems" in filters and filters["annotation_systems"][0] != "":
        op="notin"
        if not "annotation_system_notin_check" in filters:
            op="in"
        # end if
        kwargs["systems"] = {"filter": [], "op": op}
        i = 0
        for annotation_system in filters["annotation_systems"]:
            kwargs["systems"]["filter"].append(annotation_system)
            i+=1
        # end for
    # end if
    if filters["dim_signature"][0] != "":
        op="notlike"
        if not "dim_signature_notlike_check" in filters:
            op="like"
        # end if
        kwargs["dim_signatures"] = {"filter": filters["dim_signature"][0], "op": filters["dim_signature_operator"][0]}
    # end if
    elif "dim_signatures" in filters and filters["dim_signatures"][0] != "":
        op="notin"
        if not "dim_signature_notin_check" in filters:
            op="in"
        # end if
        kwargs["dim_signatures"] = {"filter": [], "op": op}
        i = 0
        for dim_signature in filters["dim_signatures"]:
            kwargs["dim_signatures"]["filter"].append(dim_signature)
            i+=1
        # end for
    # end if

    # Query restrictions
    if filters["order_by"][0] != "":
        descending = True
        if not "order_descending" in filters:
            descending = False
        # end if
        kwargs["order_by"] = {"field": filters["order_by"][0], "descending": descending}
    # end if

    if filters["limit"][0] != "":
        kwargs["limit"] = filters["limit"][0]
    # end if

    if filters["offset"][0] != "":
        kwargs["offset"] = filters["offset"][0]
    # end if

    annotation_cnfs = query.get_annotation_cnfs(**kwargs)

    return annotation_cnfs

@bp.route("/query-jsonify-annotation-cnfs-by-name")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_annotation_cnfs_by_name():
    """
    Query all the annotation configurations.
    """
    current_app.logger.debug("Query annotation configurations")
    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["names"] = {"filter": "%" + search + "%", "op": "like"}
    
    annotation_cnfs = query.get_annotation_cnfs(**kwargs)
    jsonified_annotation_cnfs = [annotation_cnf.jsonify() for annotation_cnf in annotation_cnfs]
    return jsonify(jsonified_annotation_cnfs)

@bp.route("/query-jsonify-annotation-cnfs-by-system")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_annotation_cnfs_by_system():
    """
    Query all the annotation configurations.
    """
    current_app.logger.debug("Query annotation configurations")
    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["systems"] = {"filter": "%" + search + "%", "op": "like"}
    
    annotation_cnfs = query.get_annotation_cnfs(**kwargs)
    jsonified_annotation_cnfs = [annotation_cnf.jsonify() for annotation_cnf in annotation_cnfs]
    return jsonify(jsonified_annotation_cnfs)

@bp.route("/query-jsonify-keys")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_keys():
    """
    Query all the keys.
    """
    current_app.logger.debug("Query event keys")
    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["keys"] = {"filter": search, "op": "=="}

    keys = query.get_event_keys(**kwargs)
    jsonified_keys = [key.jsonify() for key in keys]
    return jsonify(jsonified_keys)

@bp.route("/query-ers", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_ers_and_render():
    """
    Query explicit references and render.
    """
    current_app.logger.debug("Query explicit references and render")
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
        filters["offset"] = [""]
        
        if "query_explicit_refs" in filters:
            ers = query_ers(filters)
            return render_template("eboa_nav/explicit_references_nav.html", ers=ers, filters=filters)
        else:
            er_alerts = query_er_alerts(filters)
            return render_template("eboa_nav/explicit_reference_alerts_nav.html", alerts=er_alerts, filters=filters)
        # end if
    # end if
    
    return render_template("eboa_nav/query_explicit_references.html")

@bp.route("/query-ers-pages", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_ers_pages():
    """
    Query explicit references using pages and render.
    """
    current_app.logger.debug("Query explicit references using pages and render")
    filters = request.json
    ers = query_ers(filters)

    return render_template("eboa_nav/explicit_references_nav.html", ers=ers, filters=filters)

def query_ers(filters):
    """
    Query explicit references.
    """
    current_app.logger.debug("Query explicit references")

    kwargs = set_filters_for_query_ers_or_er_alerts(filters)

    ers = query.get_explicit_refs(**kwargs)

    return ers

def query_er_alerts(filters):
    """
    Query explicit reference alerts.
    """
    current_app.logger.debug("Query explicit reference alerts")

    er_kwargs = set_filters_for_query_ers_or_er_alerts(filters)

    alert_kwargs = set_specific_alert_filters(filters)

    kwargs = {**er_kwargs, **alert_kwargs}

    er_alerts = query.get_explicit_ref_alerts(**kwargs)

    return er_alerts

def set_filters_for_query_ers_or_er_alerts(filters):
    """
    Set filter for query ers or query er alerts.
    """
    kwargs = {}

    # Wether is query er or query er alerts
    groups_filter_name = "groups" 
    if "query_explicit_ref_alerts" in filters: 
        groups_filter_name = "explicit_ref_groups"
    # end if    
    
    if filters["er"][0] != "":
        op="notlike"
        if not "er_notlike_check" in filters:
            op="like"
        # end if
        kwargs["explicit_refs"] = {"filter": filters["er"][0], "op": filters["er_operator"][0]}
    # end if
    elif "ers" in filters and filters["ers"][0] != "":
        op="notin"
        if not "er_notin_check" in filters:
            op="in"
        # end if
        kwargs["explicit_refs"] = {"filter": [], "op": op}
        i = 0
        for er in filters["ers"]:
            kwargs["explicit_refs"]["filter"].append(er)
            i+=1
        # end for
    # end if
    if filters["group"][0] != "":
        op="notlike"
        if not "group_notlike_check" in filters:
            op="like"
        # end if
        kwargs[groups_filter_name] = {"filter": filters["group"][0], "op": filters["group_operator"][0]}
    # end if
    elif "groups" in filters and filters["groups"][0] != "":
        op="notin"
        if not "group_notin_check" in filters:
            op="in"
        # end if
        kwargs[groups_filter_name] = {"filter": [], "op": op}
        i = 0
        for group in filters["groups"]:
            kwargs[groups_filter_name]["filter"].append(group)
            i+=1
        # end for
    # end if
    if filters["source"][0] != "":
        op="notlike"
        if not "source_notlike_check" in filters:
            op="like"
        # end if
        kwargs["sources"] = {"filter": filters["source"][0], "op": filters["source_operator"][0]}
    # end if
    elif "sources" in filters and filters["sources"][0] != "":
        op="notin"
        if not "source_notin_check" in filters:
            op="in"
        # end if
        kwargs["sources"] = {"filter": [], "op": op}
        i = 0
        for source in filters["sources"]:
            kwargs["sources"]["filter"].append(source)
            i+=1
        # end for
    # end if
    if filters["ingestion_time"][0] != "":
        kwargs["explicit_ref_ingestion_time_filters"] = []
        i = 0
        operators = filters["ingestion_time_operator"]
        for ingestion_time in filters["ingestion_time"]:
            kwargs["explicit_ref_ingestion_time_filters"].append({"date": ingestion_time, "op": operators[i]})
            i+=1
        # end for
    # end if

    ####
    # Event filters
    ####
    if filters["key"][0] != "":
        op="notlike"
        if not "key_notlike_check" in filters:
            op="like"
        # end if
        kwargs["keys"] = {"filter": filters["key"][0], "op": filters["key_operator"][0]}
    # end if
    elif "keys" in filters and filters["keys"][0] != "":
        op="notin"
        if not "key_notin_check" in filters:
            op="in"
        # end if
        kwargs["keys"] = {"filter": [], "op": op}
        i = 0
        for key in filters["keys"]:
            kwargs["keys"]["filter"].append(key)
            i+=1
        # end for
    # end if
    if filters["event_value_name"][0] != "":
        value_operators = filters["event_value_operator"]
        value_types = filters["event_value_type"]
        values = filters["event_value"]
        value_name_ops = filters["event_value_name_op"]
        kwargs["event_value_filters"] = []
        i = 0
        for value_name in filters["event_value_name"]:
            if len(value_name) > 0 and value_name[0] != "":
                if (values[i] == "" and value_types[i] == "text") or (values[i][0] != "" and value_types[i] != "object"):
                    kwargs["event_value_filters"].append({"name": {"op": value_name_ops[i], "filter": value_name},
                                                          "type": value_types[i],
                                                          "value": {"op": value_operators[i], "filter": values[i]}})
                else:
                    kwargs["event_value_filters"].append({"name": {"op": value_name_ops[i], "filter": value_name},
                                                          "type": value_types[i]})
            # end if
            i+=1
        # end for
    # end if
    if filters["gauge_name"][0] != "":
        op="notlike"
        if not "gauge_name_notlike_check" in filters:
            op="like"
        # end if
        kwargs["gauge_names"] = {"filter": filters["gauge_name"][0], "op": filters["gauge_name_operator"][0]}
    # end if
    elif "gauge_names" in filters and filters["gauge_names"][0] != "":
        op="notin"
        if not "gauge_name_notin_check" in filters:
            op="in"
        # end if
        kwargs["gauge_names"] = {"filter": [], "op": op}
        i = 0
        for gauge_name in filters["gauge_names"]:
            kwargs["gauge_names"]["filter"].append(gauge_name)
            i+=1
        # end for
    # end if
    if filters["gauge_system"][0] != "":
        op="notlike"
        if not "gauge_system_notlike_check" in filters:
            op="like"
        # end if
        kwargs["gauge_systems"] = {"filter": filters["gauge_system"][0], "op": filters["gauge_system_operator"][0]}
    # end if
    elif "gauge_systems" in filters and filters["gauge_systems"][0] != "":
        op="notin"
        if not "gauge_system_notin_check" in filters:
            op="in"
        # end if
        kwargs["gauge_systems"] = {"filter": [], "op": op}
        i = 0
        for gauge_system in filters["gauge_systems"]:
            kwargs["gauge_systems"]["filter"].append(gauge_system)
            i+=1
        # end for
    # end if
    if filters["start"][0] != "":
        kwargs["start_filters"] = []
        i = 0
        operators = filters["start_operator"]
        for start in filters["start"]:
            kwargs["start_filters"].append({"date": start, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["stop"][0] != "":
        kwargs["stop_filters"] = []
        i = 0
        operators = filters["stop_operator"]
        for stop in filters["stop"]:
            kwargs["stop_filters"].append({"date": stop, "op": operators[i]})
            i+=1
        # end for
    # end if
    if filters["event_duration"][0] != "":
        kwargs["duration_filters"] = []
        i = 0
        operators = filters["event_duration_operator"]
        for event_duration in filters["event_duration"]:
            kwargs["duration_filters"].append({"float": float(event_duration), "op": operators[i]})
            i+=1
        # end for
    # end if

    ####
    # Annotation filters
    ####
    if filters["annotation_value_name"][0] != "":
        value_operators = filters["annotation_value_operator"]
        value_types = filters["annotation_value_type"]
        values = filters["annotation_value"]
        value_name_ops = filters["annotation_value_name_op"]
        kwargs["annotation_value_filters"] = []
        i = 0
        for value_name in filters["annotation_value_name"]:
            if len(value_name) > 0 and value_name[0] != "":
                if (values[i] == "" and value_types[i] == "text") or (values[i][0] != "" and value_types[i] != "object"):
                    kwargs["annotation_value_filters"].append({"name": {"op": value_name_ops[i], "filter": value_name},
                                                          "type": value_types[i],
                                                          "value": {"op": value_operators[i], "filter": values[i]}})
                else:
                    kwargs["annotation_value_filters"].append({"name": {"op": value_name_ops[i], "filter": value_name},
                                                          "type": value_types[i]})
            # end if
            i+=1
        # end for
    # end if
    if filters["annotation_name"][0] != "":
        op="notlike"
        if not "annotation_name_notlike_check" in filters:
            op="like"
        # end if
        kwargs["annotation_cnf_names"] = {"filter": filters["annotation_name"][0], "op": filters["annotation_name_operator"][0]}
    # end if
    elif "annotation_names" in filters and filters["annotation_names"][0] != "":
        op="notin"
        if not "annotation_name_notin_check" in filters:
            op="in"
        # end if
        kwargs["annotation_cnf_names"] = {"filter": [], "op": op}
        i = 0
        for annotation_name in filters["annotation_names"]:
            kwargs["annotation_cnf_names"]["filter"].append(annotation_name)
            i+=1
        # end for
    # end if
    if filters["annotation_system"][0] != "":
        op="notlike"
        if not "annotation_system_notlike_check" in filters:
            op="like"
        # end if
        kwargs["annotation_cnf_systems"] = {"filter": filters["annotation_system"][0], "op": filters["annotation_system_operator"][0]}
    # end if
    elif "annotation_systems" in filters and filters["annotation_systems"][0] != "":
        op="notin"
        if not "annotation_system_notin_check" in filters:
            op="in"
        # end if
        kwargs["annotation_cnf_systems"] = {"filter": [], "op": op}
        i = 0
        for annotation_system in filters["annotation_systems"]:
            kwargs["annotation_cnf_systems"]["filter"].append(annotation_system)
            i+=1
        # end for
    # end if

    # Query restrictions
    if filters["order_by"][0] != "":
        descending = True
        if not "order_descending" in filters:
            descending = False
        # end if
        kwargs["order_by"] = {"field": filters["order_by"][0], "descending": descending}
    # end if

    if filters["limit"][0] != "":
        kwargs["limit"] = filters["limit"][0]
    # end if

    if filters["offset"][0] != "":
        kwargs["offset"] = filters["offset"][0]
    # end if

    return kwargs

@bp.route("/query-er/<uuid:explicit_ref_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_er(explicit_ref_uuid):
    """
    Query explicit reference corresponding to the UUID received.
    """
    current_app.logger.debug("Query explicit reference")
    er = query.get_explicit_refs(explicit_ref_uuids={"filter": [explicit_ref_uuid], "op": "in"})

    filters = {}
    filters["offset"] = [""]
    filters["limit"] = ["100"]
    
    return render_template("eboa_nav/explicit_references_nav.html", ers=er, filters=filters)

@bp.route("/query-er-by-name/<string:name>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_er_by_name(name):
    """
    Query explicit reference corresponding to the name received.
    """
    current_app.logger.debug("Query explicit reference by name")
    er = query.get_explicit_refs(explicit_refs={"filter": name, "op": "=="})

    filters = {}
    filters["offset"] = [""]
    filters["limit"] = ["100"]
    
    return render_template("eboa_nav/explicit_references_nav.html", ers=er, filters=filters)

@bp.route("/query-er-links/<uuid:explicit_ref_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_er_links_and_render(explicit_ref_uuid):
    """
    Query explicit references linked to the explicit reference corresponding to the UUID received and render.
    """
    current_app.logger.debug("Query explicit reference links and render")
    links = query_er_links(explicit_ref_uuid)
    ers = links["prime_explicit_refs"] + [link["explicit_ref"] for link in links["explicit_refs_linking"]] + [link["explicit_ref"] for link in links["linked_explicit_refs"]]
    return render_template("eboa_nav/linked_explicit_references_nav.html", links=links, ers=ers)

def query_er_links(explicit_ref_uuid):
    """
    Query explicit references linked to the explicit reference corresponding to the UUID received.
    """
    current_app.logger.debug("Query explicit reference links")
    links = query.get_linked_explicit_refs_details(explicit_ref_uuid=explicit_ref_uuid, back_ref = True)

    return links

@bp.route("/query-jsonify-ers")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_ers():
    """
    Query all the ers.
    """
    current_app.logger.debug("Query explicit references")
    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["explicit_refs"] = {"filter": search, "op": "=="}

    ers = query.get_explicit_refs(**kwargs)
    jsonified_ers = [er.jsonify() for er in ers]
    return jsonify(jsonified_ers)

@bp.route("/query-jsonify-er-groups")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_er_groups():
    """
    Query all the ers groups.
    """
    current_app.logger.debug("Query explicit reference groups")
    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["names"] = {"filter": "%" + search + "%", "op": "like"}

    er_groups = query.get_explicit_refs_groups(**kwargs)
    jsonified_er_groups = [er_group.jsonify() for er_group in er_groups]
    return jsonify(jsonified_er_groups)

@bp.route("/query-dim-signatures", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_dim_signatures_and_render():
    """
    Query DIM signatures amd render.
    """
    current_app.logger.debug("Query DIM signatures and render")
    if request.method == "POST":
        filters = request.form.to_dict(flat=False).copy()
        filters["offset"] = [""]
        dim_signatures = query_dim_signatures(filters)

        return render_template("eboa_nav/dim_signatures_nav.html", dim_signatures=dim_signatures, filters=filters)
    # end if

    return render_template("eboa_nav/query_dim_signatures.html")

@bp.route("/query-dim-signatures-pages", methods=["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_dim_signatures_pages():
    """
    Query DIM signatures using pages and render.
    """
    current_app.logger.debug("Query DIM signatures using pages and render")

    filters = request.json
    dim_signatures = query_dim_signatures(filters)

    return render_template("eboa_nav/dim_signatures_nav.html", dim_signatures=dim_signatures, filters=filters)

def query_dim_signatures(filters):
    """
    Query DIM signatures.
    """
    current_app.logger.debug("Query DIM signatures")
    kwargs = {}
    if filters["dim_signature"][0] != "":
        op="notlike"
        if not "dim_signature_notlike_check" in filters:
            op="like"
        # end if
        kwargs["dim_signatures"] = {"filter": filters["dim_signature"][0], "op": filters["dim_signature_operator"][0]}
    # end if
    elif "dim_signatures" in filters and filters["dim_signatures"][0] != "":
        op="notin"
        if not "dim_signature_notin_check" in filters:
            op="in"
        # end if
        kwargs["dim_signatures"] = {"filter": [], "op": op}
        i = 0
        for dim_signature in filters["dim_signatures"]:
            kwargs["dim_signatures"]["filter"].append(dim_signature)
            i+=1
        # end for
    # end if

    # Query restrictions
    if filters["order_by"][0] != "":
        descending = True
        if not "order_descending" in filters:
            descending = False
        # end if
        kwargs["order_by"] = {"field": filters["order_by"][0], "descending": descending}
    # end if

    if filters["limit"][0] != "":
        kwargs["limit"] = filters["limit"][0]
    # end if

    if filters["offset"][0] != "":
        kwargs["offset"] = filters["offset"][0]
    # end if

    dim_signatures = query.get_dim_signatures(**kwargs)

    return dim_signatures

@bp.route("/query-jsonify-dim-signatures")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_dim_signatures():
    """
    Query all the DIM signatures.
    """
    current_app.logger.debug("Query DIM signatures")
    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["dim_signatures"] = {"filter": "%" + search + "%", "op": "like"}

    dim_signatures = query.get_dim_signatures(**kwargs)
    jsonified_dim_signatures = [dim_signature.jsonify() for dim_signature in dim_signatures]
    return jsonify(jsonified_dim_signatures)

@bp.route("/treat-data", methods = ["POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator")
def treat_data():
    """
    Send data to the EBOA to be treated
    """
    current_app.logger.debug("Treat data")
    if request.headers['Content-Type'] != 'application/json':
        raise
    # end if

    data = request.get_json()
    returned_values = engine.treat_data(data)
    exit_information = {
        "returned_values": returned_values
    }
    return jsonify(exit_information)

@bp.route("/query-alerts-pages", methods=["GET", "POST"])
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_alerts_pages():
    """
    Query alerts using pages and render.
    """
    current_app.logger.debug("Query alerts using pages and render")
    filters = request.json

    if "query_event_alerts" in filters:
        alerts = query_event_alerts(filters)
        template = "eboa_nav/event_alerts_nav.html"
    elif "query_annotation_alerts" in filters:
        alerts = query_annotation_alerts(filters)
        template = "eboa_nav/annotation_alerts_nav.html"
    elif "query_source_alerts" in filters:
        alerts = query_source_alerts(filters)
        template = "eboa_nav/source_alerts_nav.html"
    elif "query_explicit_ref_alerts" in filters:
        alerts = query_er_alerts(filters)
        template = "eboa_nav/explicit_reference_alerts_nav.html"
    # end if
    return render_template(template, alerts=alerts, filters=filters)

@bp.route("/query-<string:entity>-alert/<uuid:alert_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_entity_alert_and_render(entity, alert_uuid):
    """
    Query alert associated to the entity with UUID alert_uuid.

    :param entity: entity whose alerts are requested
    :type entity: str
    :param alert_uuid: UUID of the alert
    :type alert_uuid: str

    :return: template with the shown alert
    :rtype: template
    """

    kwargs = {}
    if entity == "event":
        kwargs["event_alert_uuids"] = {"filter": str(alert_uuid), "op": "=="}
        alerts = query.get_event_alerts(**kwargs)
        template = "eboa_nav/event_alerts_nav.html"
    elif entity == "annotation":
        kwargs["annotation_alert_uuids"] = {"filter": str(alert_uuid), "op": "=="}
        alerts = query.get_annotation_alerts(**kwargs)
        template = "eboa_nav/annotation_alerts_nav.html"
    elif entity == "source":
        kwargs["source_alert_uuids"] = {"filter": str(alert_uuid), "op": "=="}
        alerts = query.get_source_alerts(**kwargs)
        template = "eboa_nav/source_alerts_nav.html"
    else:
        kwargs["explicit_ref_alert_uuids"] = {"filter": str(alert_uuid), "op": "=="}
        alerts = query.get_explicit_ref_alerts(**kwargs)
        template = "eboa_nav/explicit_reference_alerts_nav.html"
    # end if
    
    return render_template(template, alerts=alerts, filters=kwargs)

@bp.route("/query-<string:entity>-alerts/<uuid:entity_uuid>")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_entity_alerts_and_render(entity, entity_uuid):
    """
    Query alerts associated to the entity with UUID entity_uuid.

    :param entity: entity whose alerts are requested
    :type entity: str
    :param entity_uuid: UUID of the entity whose alerts are requested
    :type entity_uuid: str

    :return: template with the shown alerts
    :rtype: template
    """

    kwargs = {}
    if entity == "event":
        kwargs["event_uuids"] = {"filter": str(entity_uuid), "op": "=="}
        alerts = query.get_event_alerts(**kwargs)
        template = "eboa_nav/event_alerts_nav.html"
    elif entity == "annotation":
        kwargs["annotation_uuids"] = {"filter": str(entity_uuid), "op": "=="}
        alerts = query.get_annotation_alerts(**kwargs)
        template = "eboa_nav/annotation_alerts_nav.html"
    elif entity == "source":
        kwargs["source_uuids"] = {"filter": str(entity_uuid), "op": "=="}
        alerts = query.get_source_alerts(**kwargs)
        template = "eboa_nav/source_alerts_nav.html"
    else:
        kwargs["explicit_ref_uuids"] = {"filter": str(entity_uuid), "op": "=="}
        alerts = query.get_explicit_ref_alerts(**kwargs)
        template = "eboa_nav/explicit_reference_alerts_nav.html"
    # end if
    
    return render_template(template, alerts=alerts, filters=kwargs)

@bp.route("/get-alert-severity")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def get_alert_severities():
    """
    Get the alert severities defined in the EBOA component.
    """
    current_app.logger.debug("Get alert severities")
    return jsonify(eboa_alerts.alert_severity_codes)

@bp.route("/query-jsonify-alerts-by-name")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_alerts_by_name():
    """
    Query all the alerts by name.
    """
    current_app.logger.debug("Query alerts by name")
    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["names"] = {"filter": search, "op": "=="}

    alerts = query.get_alerts(**kwargs)
    jsonified_alerts = [alert.jsonify() for alert in alerts]
    return jsonify(jsonified_alerts)

@bp.route("/query-jsonify-alerts-by-group")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_alerts_by_group():
    """
    Query all the alerts by group.
    """
    current_app.logger.debug("Query alerts by group")
    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["groups"] = {"filter": search, "op": "=="}

    alerts = query.get_alerts(**kwargs)
    jsonified_alerts = [alert.jsonify() for alert in alerts]
    return jsonify(jsonified_alerts)

@bp.route("/query-jsonify-<string:entity>-alerts-by-generator")
@auth_required()
@roles_accepted("administrator", "service_administrator", "operator", "analyst", "operator_observer")
def query_jsonify_entity_alerts_by_generator(entity):
    """
    Query all the entity alerts by generator.
    """
    current_app.logger.debug("Query entity alerts by generator")
    # Get limit and offset values
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    search = request.args.get("search")

    # Set the filters for the query
    kwargs = {}
    kwargs["limit"] = limit
    kwargs["offset"] = offset
    kwargs["generators"] = {"filter": search, "op": "=="}

    if entity == "event":
        event_alerts = query.get_event_alerts(**kwargs)
        jsonified_alerts = [event_alert.jsonify() for event_alert in event_alerts]
    elif entity == "annotation":
        annotation_alerts = query.get_annotation_alerts(**kwargs)
        jsonified_alerts = [annotation_alert.jsonify() for annotation_alert in annotation_alerts]
    elif entity == "source":
        source_alerts = query.get_source_alerts(**kwargs)
        jsonified_alerts = [source_alert.jsonify() for source_alert in source_alerts]
    elif entity == "explicit-ref":
        er_alerts = query.get_explicit_ref_alerts(**kwargs)
        jsonified_alerts = [er_alert.jsonify() for er_alert in er_alerts]
    return jsonify(jsonified_alerts)
