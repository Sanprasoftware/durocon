frappe.ui.form.on('Sales Order', {
    company: function(frm) {
        if (frm.doc.company === "DUROCON CONCARE PVT LTD") {

            // Set main cost center
            frm.set_value("cost_center", "Main - DC");
            frm.set_value("set_warehouse", "Finished Goods - DC");
            // Set warehouse + cost center in items
            frm.doc.items.forEach(function(row) {
                row.cost_center = "Main - DC";
            });

            frm.refresh_field("items");
        }
    }
});
