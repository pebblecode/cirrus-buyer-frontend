# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import abort, render_template, request, current_app

from dmutils.formats import get_label_for_lot_param, dateformat
from dmapiclient import HTTPError
from dmutils.formats import LOTS

from ...main import main
from ..forms.order_forms import OrderForm
from ...presenters.search_presenters import (
    filters_for_lot,
    set_filter_states,
)
from ...presenters.search_results import SearchResults
from ...presenters.search_summary import SearchSummary
from ...presenters.service_presenters import Service
from ...helpers.search_helpers import (
    get_keywords_from_request, pagination,
    get_page_from_request, query_args_for_pagination,
    get_lot_from_request, build_search_query,
    clean_request_args
)

from ...exceptions import AuthException
from app import search_api_client, data_api_client, content_loader

from datetime import date
import locale


@main.route('/inoket')
def index_g_cloud():
    return render_template('index-g-cloud.html')


@main.route('/inoket/services/<service_id>')
def get_service_by_id(service_id):
    try:
        service = data_api_client.get_service(service_id)
        if service is None:
            abort(404, "Service ID '{}' can not be found".format(service_id))
        if service['services']['frameworkStatus'] not in ("live", "expired"):
            abort(404, "Service ID '{}' can not be found".format(service_id))

        service_data = service['services']
        service_view_data = Service(
            service_data,
            content_loader.get_builder('inoket-1', 'display_service').filter(
                service_data
            )
        )

        try:
            # get supplier data and add contact info to service object
            supplier = data_api_client.get_supplier(
                service_data['supplierId']
            )
            supplier_data = supplier['suppliers']
            service_view_data.meta.set_contact_attribute(
                supplier_data['contactInformation'][0].get('contactName'),
                supplier_data['contactInformation'][0].get('phoneNumber'),
                supplier_data['contactInformation'][0].get('email')
            )

        except HTTPError as e:
            abort(e.status_code)

        service_unavailability_information = None
        status_code = 200
        if service['serviceMadeUnavailableAuditEvent'] is not None:
            service_unavailability_information = {
                'date': dateformat(service['serviceMadeUnavailableAuditEvent']['createdAt']),
                'type': service['serviceMadeUnavailableAuditEvent']['type']
            }
            # mark the resource as unavailable in the headers
            status_code = 410

        return render_template(
            'service.html',
            service=service_view_data,
            service_unavailability_information=service_unavailability_information,
            lot=service_view_data.lot.lower(),
            lot_label=get_label_for_lot_param(service_view_data.lot.lower()),
            service_id=service_id), status_code
    except AuthException:
        abort(500, "Application error")
    except KeyError:
        abort(404, "Service ID '%s' can not be found" % service_id)
    except HTTPError as e:
        abort(e.status_code)


def format_date():
    return date.today().strftime('%d/%m/%Y')


@main.route('/order', methods=['GET', 'POST'])
def order():
    service_id = request.args.get('service_id')
    service_title = request.args.get('service_title')
    supplierName = request.args.get('supplierName')
    form = OrderForm()
    if form.validate_on_submit():
        return render_template(
            'order-received.html',
            service_id=service_id,
            service_title=service_title,
            supplier_name=supplierName,
            po_number=form.po_number.data,
            date=format_date(),
            email=form.email_address.data,
            amount='{:,.2f}'.format(form.amount.data)
            )

    return render_template(
        'order.html',
        form=form,
        service_id=service_id,
        service_title=service_title,
        supplierName=supplierName), 200


@main.route('/order-received')
def order_received():
    return 'Thank You', 200

@main.route('/buyers-guide')
def buyers_guide():
    return render_template(
        'buyer_guide.html',
        title='Buyer Guide'
    )

@main.route('/supply-guide')
def suppliers_guide():
    return render_template(
        'supplier_guide.html',
        title='Supplier Guide'
    )

@main.route('/inoket/search')
def search():
    content_builder = content_loader.get_builder('inoket-1', 'search_filters')
    filters = filters_for_lot(
        get_lot_from_request(request),
        content_builder
    )

    response = search_api_client.search_services(
        index='inoket-1',
        **build_search_query(request, filters, content_builder)
    )

    search_results_obj = SearchResults(response)

    pagination_config = pagination(
        search_results_obj.total,
        current_app.config["DM_SEARCH_PAGE_SIZE"],
        get_page_from_request(request)
    )

    search_summary = SearchSummary(
        response['meta']['total'],
        clean_request_args(request.args, filters),
        filters
    )

    set_filter_states(filters, request)
    current_lot = get_lot_from_request(request)

    # import ipdb; ipdb.set_trace();
    return render_template(
        'search.html',
        current_lot=current_lot,
        current_lot_label=get_label_for_lot_param(current_lot) if current_lot else None,
        filters=filters,
        lots=LOTS,
        pagination=pagination_config,
        search_keywords=get_keywords_from_request(request),
        search_query=query_args_for_pagination(request.args),
        services=search_results_obj.search_results,
        summary=search_summary.markup(),
        title='Search results',
        total=search_results_obj.total
    )
