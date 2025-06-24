import traceback
import frappe
import requests

@frappe.whitelist()
def fetch_flight_details(flight_number):
    api_key = frappe.db.get_single_value("Flight Settings", "api_key")
    if not api_key:
        frappe.throw("API Key not found in Flight Settings.")

    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': api_key,
        'flight_iata': flight_number
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            frappe.throw(f"API Error: {response.status_code} - {response.text}")
        
        data = response.json()
        if not data.get('data'):
            return {"error": "No data found for this flight number."}

        flight = data['data'][0]
        
         # ✅ Add this status mapping block:
        status_map = {
            "scheduled": "Scheduled",
            "delayed": "Delayed",
            "active": "En Route",
            "landed": "Landed",
            "cancelled": "Cancelled"
        }

        raw_status = flight['flight_status']
        mapped_status = status_map.get(raw_status.lower(), "Scheduled")


        return {
            "flight_number": flight['flight']['iata'],
            "airline": flight['airline']['name'],
            "origin": flight['departure']['airport'],
            "destination": flight['arrival']['airport'],
            "scheduled_departure": flight['departure']['scheduled'],
            "scheduled_arrival": flight['arrival']['scheduled'],
            "estimated_departure": flight['departure']['estimated'],
            "estimated_arrival": flight['arrival']['estimated'],
            "actual_departure": flight['departure']['actual'],
            "actual_arrival": flight['arrival']['actual'],
            "gate": flight['departure'].get('gate'),
            "terminal": flight['departure'].get('terminal'),
            "status": mapped_status,
            "delay_duration": flight['departure'].get('delay'),
            "latitude": flight['live']['latitude'] if flight.get('live') else None,
            "longitude": flight['live']['longitude'] if flight.get('live') else None
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Flight API Error")
        return {"error": str(e)}


@frappe.whitelist()
def update_flight_status(docname):
    doc = frappe.get_doc("Flight", docname)
    return _update_flight_status(doc)


def _update_flight_status(flight_doc):
    try:
        flight_number = flight_doc.flight_number
        if not flight_number:
            frappe.throw("Flight number is required.")

        data = fetch_flight_details(flight_number)
        if data.get("error"):
            frappe.throw(data["error"])

        for key in [
            "airline", "origin", "destination", "scheduled_departure",
            "scheduled_arrival", "estimated_departure", "estimated_arrival",
            "actual_departure", "actual_arrival", "gate", "terminal",
            "status", "delay_duration", "latitude", "longitude"
        ]:
            setattr(flight_doc, key, data.get(key))

        flight_doc.save(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "msg": "Flight updated successfully."}

    except Exception as e:
        frappe.log_error(traceback.format_exc(), "Flight Update Error")
        return {"error": str(e)}

def sync_flight_statuses():
    try:
        flights = frappe.get_all("Flight", filters={"status": ["not in", ["Landed", "Cancelled"]]}, fields=["name"])
        for flight in flights:
            try:
                doc = frappe.get_doc("Flight", flight["name"])
                _update_flight_status(doc)
            except Exception as e:
                frappe.log_error(traceback.format_exc(), f"Sync Error for Flight {flight['name']}")
    except Exception as e:
        frappe.log_error(traceback.format_exc(), "Flight Sync Scheduler Error")