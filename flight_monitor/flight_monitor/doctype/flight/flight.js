// Copyright (c) 2025, chirag and contributors
// For license information, please see license.txt

frappe.ui.form.on("Flight", {
    refresh(frm) {
        if (frm.doc.status === "Scheduled") {
            frm.add_custom_button(__("Check Flight Status"), function () {
                frappe.call({
                    method: "flight_monitor.flight_monitor.doctype.flight.flight.check_flight_status",
                    args: {
                        flight_id: frm.doc.name,
                    },
                    callback: function (r) {
                        if (r.message) {
                            frappe.msgprint(__("Flight Status: {0}", [r.message]));
                        } else {
                            frappe.msgprint(__("No status available for this flight."));
                        }
                    },
                });
            });
        }
    },
    });
