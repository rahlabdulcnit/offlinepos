frappe.pages['pos_checkout'].on_page_load = function(wrapper) {
    new PointOfSale(wrapper);
};

class PointOfSale {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: 'Point of Sale',
            single_column: true
        });

        this.state = {
            cart: [],
            pos_profile: null,
            all_items: [],
            payment_modes: [],
            pos_shift: null
        };

        this.setup_dom();
        this.bind_events();
        this.show_shift_modal();
    }

    setup_dom() {
        this.page.main.html(frappe.render_template('pos_checkout', {}));
        this.dom = {
            item_grid: this.wrapper.querySelector('#item-grid'),
            cart_list: this.wrapper.querySelector('#cart-items-list'),
            profile_selector: this.wrapper.querySelector('#pos-profile-selector'),
            search_input: this.wrapper.querySelector('#item-search-input'),
            subtotal_val: this.wrapper.querySelector('#subtotal-value'),
            grand_total_val: this.wrapper.querySelector('#grand-total-value'),
            payment_lines: this.wrapper.querySelector('#payment-lines'),
            add_payment_btn: this.wrapper.querySelector('#add-payment-btn'),
            paid_amount_val: this.wrapper.querySelector('#paid-amount-value'),
            due_amount_val: this.wrapper.querySelector('#due-amount-value'),
            change_amount_val: this.wrapper.querySelector('#change-amount-value'),
            submit_btn: this.wrapper.querySelector('#submit-button'),
            close_shift_btn: this.wrapper.querySelector('#close-shift-button')
        };
    }

    bind_events() {
        this.dom.item_grid.addEventListener('click', e => {
            const card = e.target.closest('.item-card');
            if (card) this.add_to_cart(card.dataset.itemCode);
        });

        this.dom.search_input.addEventListener('input', () => this.render_items());

        this.dom.cart_list.addEventListener('click', e => {
            if (e.target.dataset.action === 'increase-qty') {
                this.update_quantity(e.target.dataset.itemCode, 1);
            } else if (e.target.dataset.action === 'decrease-qty') {
                this.update_quantity(e.target.dataset.itemCode, -1);
            }
        });

        this.dom.profile_selector.addEventListener('change', e => {
            this.state.pos_profile = e.target.value;
            this.validate_submission();
        });

        this.dom.add_payment_btn.addEventListener('click', () => this.add_payment_line());
        this.dom.payment_lines.addEventListener('input', () => this.calculate_totals());

        this.dom.submit_btn.addEventListener('click', () => this.process_submission());

        this.dom.close_shift_btn?.addEventListener('click', () => this.show_close_shift_modal());
    }

    async show_shift_modal() {
        const modal = new frappe.ui.Dialog({
            title: 'Start POS Shift',
            fields: [
                {
                    label: 'POS Profile',
                    fieldname: 'pos_profile',
                    fieldtype: 'Link',
                    options: 'POS Profile',
                    reqd: 1
                },
                {
                    label: 'User',
                    fieldname: 'user',
                    fieldtype: 'Link',
                    options: 'User',
                    default: frappe.session.user,
                    reqd: 1
                },
                {
                    label: 'Opening Amount',
                    fieldname: 'opening_amount',
                    fieldtype: 'Currency',
                    default: 0,
                    reqd: 1
                }
            ],
            primary_action_label: 'Start Shift',
            primary_action: async (values) => {
                const res = await frappe.call({
                    method: 'frappe.client.insert',
                    args: {
                        doc: {
                            doctype: 'POS  Shift',
                            pos_profile: values.pos_profile,
                            user: values.user,
                            opening_amount: values.opening_amount,
                            status: 'Open',
                            start_time: frappe.datetime.now_datetime()
                        }
                    }
                });

                this.state.pos_profile = values.pos_profile;
                this.state.pos_shift = res.message.name;
                modal.hide();

                this.load_initial_data();
            }
        });

        modal.show();
    }

    async show_close_shift_modal() {
        const result = await frappe.call({
            method: 'custom_pos.custom_pos.page.pos_checkout.pos_checkout.get_shift_sales_total',
            args: { shift_name: this.state.pos_shift }
        });

        const { total_sales, opening_amount } = result.message;
        const closing_amount = total_sales + opening_amount;
        const end_time = frappe.datetime.now_datetime();

        const modal = new frappe.ui.Dialog({
            title: 'Close POS Shift',
            fields: [
                {
                    fieldname: 'closing_amount',
                    label: 'Closing Amount',
                    fieldtype: 'Currency',
                    read_only: 1,
                    default: closing_amount
                },
                {
                    fieldname: 'end_time',
                    label: 'End Time',
                    fieldtype: 'Datetime',
                    read_only: 1,
                    default: end_time
                }
            ],
            primary_action_label: 'Close Shift',
            primary_action: async (values) => {
                await frappe.call({
                    method: 'frappe.client.set_value',
                    args: {
                        doctype: 'POS  Shift',
                        name: this.state.pos_shift,
                        fieldname: {
                            closing_amount: closing_amount,
                            end_time: end_time,
                            status: 'Closed'
                        }
                    },
                    callback: () => {
                        frappe.show_alert({ message: 'POS Shift closed successfully.', indicator: 'green' });
                        modal.hide();
                    }
                });
            }
        });

        modal.show();
    }

    async load_initial_data() {
        const response = await frappe.call("custom_pos.custom_pos.page.pos_checkout.pos_checkout.get_pos_data");
        if (response.message) {
            this.state.all_items = response.message.items;
            this.state.payment_modes = response.message.payment_modes;

            this.dom.profile_selector.innerHTML = '<option value="">Select POS Profile</option>';
            response.message.profiles.forEach(p => {
                this.dom.profile_selector.innerHTML += `<option value="${p.name}" ${p.name === this.state.pos_profile ? 'selected' : ''}>${p.profile_name}</option>`;
            });

            this.render_items();
            this.add_payment_line();
        }
    }

    render_items() {
        const search_term = this.dom.search_input.value.toLowerCase();
        const items_to_render = this.state.all_items.filter(item =>
            item.item_name.toLowerCase().includes(search_term) ||
            item.item_code.toLowerCase().includes(search_term)
        );

        this.dom.item_grid.innerHTML = items_to_render.map(item => `
            <div class="item-card" data-item-code="${item.item_code}">
                <div class="item-name">${item.item_name}</div>
                <div class="item-price">${frappe.format(item.standard_selling_rate, { fieldtype: 'Currency' })}</div>
            </div>
        `).join('');
    }

    add_to_cart(item_code) {
        const existing_item = this.state.cart.find(item => item.item_code === item_code);
        if (existing_item) {
            existing_item.qty++;
        } else {
            const item_data = this.state.all_items.find(item => item.item_code === item_code);
            this.state.cart.push({ ...item_data, qty: 1 });
        }
        this.render_cart();
    }

    update_quantity(item_code, change) {
        const item = this.state.cart.find(i => i.item_code === item_code);
        if (item) {
            item.qty += change;
            if (item.qty <= 0) {
                this.state.cart = this.state.cart.filter(i => i.item_code !== item_code);
            }
        }
        this.render_cart();
    }

    render_cart() {
        if (this.state.cart.length === 0) {
            this.dom.cart_list.innerHTML = `
                <div class="cart-empty-state">
                    <i class="fa fa-shopping-cart"></i>
                    <span>Your cart is empty</span>
                </div>`;
        } else {
            this.dom.cart_list.innerHTML = this.state.cart.map(item => `
                <div class="cart-item">
                    <div class="item-info">
                        <div>${item.item_name}</div>
                        <small>${item.qty} x ${frappe.format(item.rate || item.standard_selling_rate, { fieldtype: 'Currency' })}</small>
                    </div>
                    <div class="item-amount">${frappe.format(item.qty * (item.rate || item.standard_selling_rate), { fieldtype: 'Currency' })}</div>
                    <div class="item-controls">
                        <button class="btn btn-sm" data-action="decrease-qty" data-item-code="${item.item_code}">-</button>
                        <button class="btn btn-sm" data-action="increase-qty" data-item-code="${item.item_code}">+</button>
                    </div>
                </div>
            `).join('');
        }
        this.calculate_totals();
    }

    add_payment_line(amount = 0) {
        const options = this.state.payment_modes.map(p => `<option value="${p.name}">${p.mode_name}</option>`).join('');
        const line_html = `
            <div class="payment-line">
                <select class="form-control payment-mode-select">${options}</select>
                <input type="number" class="form-control payment-amount-input" value="${amount.toFixed(2)}" placeholder="Amount">
                <button class="btn btn-sm btn-danger" onclick="this.parentElement.remove()">×</button>
            </div>
        `;
        this.dom.payment_lines.insertAdjacentHTML('beforeend', line_html);
    }

    calculate_totals() {
        const subtotal = this.state.cart.reduce((acc, item) => acc + (item.qty * (item.rate || item.standard_selling_rate)), 0);
        const grand_total = subtotal;
        let paid_amount = 0;

        this.dom.payment_lines.querySelectorAll('.payment-amount-input').forEach(input => {
            paid_amount += flt(input.value);
        });

        const due_amount = grand_total - paid_amount;

        const payment_inputs = this.dom.payment_lines.querySelectorAll('.payment-amount-input');
        if (payment_inputs.length === 1) {
            payment_inputs[0].value = grand_total.toFixed(2);
            paid_amount = grand_total;
        }

        this.dom.subtotal_val.innerHTML = frappe.format(subtotal, { fieldtype: 'Currency' });
        this.dom.grand_total_val.innerHTML = frappe.format(grand_total, { fieldtype: 'Currency' });
        this.dom.paid_amount_val.innerHTML = frappe.format(paid_amount, { fieldtype: 'Currency' });
        this.dom.due_amount_val.innerHTML = frappe.format(due_amount > 0 ? due_amount : 0, { fieldtype: 'Currency' });
        this.dom.change_amount_val.innerHTML = frappe.format(due_amount < 0 ? -due_amount : 0, { fieldtype: 'Currency' });

        this.validate_submission();
    }

    validate_submission() {
        const grand_total = flt(this.dom.grand_total_val.innerText.replace(/[^0-9.-]+/g, ""));
        const due_amount = flt(this.dom.due_amount_val.innerText.replace(/[^0-9.-]+/g, ""));
        const is_valid = this.state.cart.length > 0 && this.state.pos_profile && due_amount <= 0 && grand_total > 0;
        this.dom.submit_btn.disabled = !is_valid;
    }

    process_submission() {
        const payments = [];
        this.dom.payment_lines.querySelectorAll('.payment-line').forEach(line => {
            const amount = flt(line.querySelector('.payment-amount-input').value);
            if (amount > 0) {
                payments.push({
                    mode: line.querySelector('.payment-mode-select').value,
                    amount: amount
                });
            }
        });

        this.dom.submit_btn.disabled = true;
        this.dom.submit_btn.innerText = 'Processing...';

        const cart_snapshot = JSON.parse(JSON.stringify(this.state.cart));

        frappe.call({
            method: "custom_pos.custom_pos.page.pos_checkout.pos_checkout.submit_pos_invoice",
            args: {
                cart_data: JSON.stringify(this.state.cart),
                pos_profile: this.state.pos_profile,
                payments_data: JSON.stringify(payments),
                pos_shift: this.state.pos_shift
            },
            callback: (r) => {
                if (r.message && r.message.status === "Success") {
                    frappe.show_alert({ message: `Invoice ${r.message.invoice_name} created successfully.`, indicator: 'green' });
                    this.print_receipt(r.message, cart_snapshot);
                    this.reset_form();
                } else {
                    frappe.show_alert({ message: `Error: ${r.message.message || 'Unknown error'}`, indicator: 'red' });
                }
            },
            error: (r) => {
                frappe.show_alert({ message: 'A server error occurred.', indicator: 'red' });
                console.error(r);
            },
            always: () => {
                this.dom.submit_btn.disabled = false;
                this.dom.submit_btn.innerText = 'Submit';
                this.validate_submission();
            }
        });
    }

    print_receipt(invoice_data, cart_data) {
        const receiptWindow = window.open('', '', 'width=400,height=600');
        const cart_html = cart_data.map(item => `
            <tr>
                <td>${item.item_name}</td>
                <td>${item.qty}</td>
                <td>${(item.rate || item.standard_selling_rate).toFixed(2)}</td>
                <td>${(item.qty * (item.rate || item.standard_selling_rate)).toFixed(2)}</td>
            </tr>
        `).join('');

        receiptWindow.document.write(`
            <html>
                <head>
                    <title>Receipt</title>
                    <style>
                        body { font-family: Arial; font-size: 12px; padding: 10px; }
                        table { width: 100%; border-collapse: collapse; }
                        th, td { border: 1px solid #ccc; padding: 5px; text-align: left; }
                    </style>
                </head>
                <body>
                    <h2 style="text-align: center;">RECEIPT</h2>
                    <p><strong>Invoice:</strong> ${invoice_data.invoice_name}</p>
                    <table>
                        <thead><tr><th>Item</th><th>Qty</th><th>Rate</th><th>Total</th></tr></thead>
                        <tbody>${cart_html}</tbody>
                    </table>
                    <p><strong>Total:</strong> ${this.dom.grand_total_val.innerText}</p>
                    <p><strong>Paid:</strong> ${this.dom.paid_amount_val.innerText}</p>
                    <p><strong>Change:</strong> ${this.dom.change_amount_val.innerText}</p>
                    <script>window.print(); window.close();</script>
                </body>
            </html>
        `);
        receiptWindow.document.close();
    }

    reset_form() {
        this.state.cart = [];
        this.render_cart();
        this.dom.payment_lines.innerHTML = '';
        this.add_payment_line();
        this.calculate_totals();
    }
}
