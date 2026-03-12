from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from flask import send_from_directory

print(os.path.exists('static/Singh_logo.png'))  # Should print True


# Import models (db is defined here, but initialized later)
from models import db, User, Rate, Vendor, RateCard, AccountGroup
# ────────────────────────────────────────────────
# Load environment variables (harmless even without .env on Railway)
# ────────────────────────────────────────────────
load_dotenv()

app = Flask(__name__)

# Secret key – must be set in Railway Variables tab
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is not set in environment variables!")

# ────────────────────────────────────────────────
# Database configuration – Railway compatible
# ────────────────────────────────────────────────
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is missing! "
        "Make sure you linked the PostgreSQL service and added the reference in Variables."
    )

# Railway sometimes uses postgres:// scheme → convert to postgresql:// (SQLAlchemy requirement)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,           # helps detect broken connections
    "pool_recycle": 3600,            # recycle connections every hour
}

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)


# ────────────────────────────────────────────────
# LOGIN ROUTE
# ────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.password_hash == password:
            session["user"] = user.role
            session["user_id"] = user.id

            if user.role == "customer":
                return redirect(url_for("customer"))
            elif user.role == "admin":
                return redirect(url_for("admin"))
        else:
            flash("Invalid username or password", "error")

    return render_template("login.html")


# ────────────────────────────────────────────────
# CUSTOMER ROUTE
# ────────────────────────────────────────────────
@app.route("/customer", methods=["GET", "POST"])
def customer():
    if "user" not in session or session["user"] != "customer":
        return redirect(url_for("login"))

    result = None
    error = None
    search_type = request.form.get("search_type", "route") if request.method == "POST" else "route"

    if request.method == "POST":
        if search_type == "route":
            from_st = request.form.get("from_station", "").strip().upper()
            to_st = request.form.get("to_station", "").strip().upper()

            if not from_st or not to_st:
                error = "Please select both From and To stations."
            else:
                # Queries RateCard table (linked from Admin Tab 3)
                rc = RateCard.query.filter_by(origin_station=from_st, dest_station=to_st).first()
                result = rc.rate_card if rc else "No rate found for this route."

        elif search_type == "train":
            train_num = request.form.get("train_number", "").strip()
            if not train_num:
                error = "Please select a train number."
            else:
                # Train search uses RateCard table
                rc = RateCard.query.filter_by(train_no=train_num).first()
                result = rc.rate_card if rc else f"No rate found for train {train_num}."
        else:
            error = "Invalid search type."

    # Unique origin stations from rate_cards for autocomplete
    origin_stations = sorted(set(
        rc.origin_station for rc in RateCard.query.with_entities(RateCard.origin_station).distinct().all()
        if rc.origin_station
    ))

    # Unique train numbers from rate_cards for autocomplete
    train_numbers = sorted(set(
        rc.train_no for rc in RateCard.query.with_entities(RateCard.train_no).distinct().all()
        if rc.train_no
    ))

    return render_template(
        "customer.html",
        result=result,
        error=error,
        search_type=search_type,
        origin_stations=origin_stations,
        train_numbers=train_numbers
    )


# ────────────────────────────────────────────────
# API: GET DESTINATIONS FOR A GIVEN ORIGIN
# ────────────────────────────────────────────────
@app.route("/api/destinations")
def api_destinations():
    """Returns list of destination stations for a given origin from rate_cards table."""
    origin = request.args.get("origin", "").strip().upper()
    if not origin:
        return jsonify([])

    rows = RateCard.query.filter_by(origin_station=origin).with_entities(RateCard.dest_station).distinct().all()
    destinations = sorted([r.dest_station for r in rows if r.dest_station])
    return jsonify(destinations)


# ────────────────────────────────────────────────
# ADMIN ROUTE
# ────────────────────────────────────────────────
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session or session["user"] != "admin":
        return redirect(url_for("login"))

    tab = request.args.get("tab", "search")
    action = request.args.get("action", "list")
    edit_id = request.args.get("edit_id")

    rate_result = None
    vendors_list = None
    message = None

    # ── Rate Search — uses RateCard table ──────────────────
    if request.method == "POST" and "search_rate" in request.form:
        from_st = request.form.get("from_station", "").strip().upper()
        to_st = request.form.get("to_station", "").strip().upper()

        rc = RateCard.query.filter_by(origin_station=from_st, dest_station=to_st).first()

        if rc:
            rate_result = {
                "rate_card": rc.rate_card,
                "train_no": rc.train_no or "N/A",
                "vehicle_type": rc.vehicle_type or "N/A",
                "days": rc.days or "N/A",
                "slr": rc.remark or ""
            }
        else:
            rate_result = {
                "rate_card": "No rate found",
                "train_no": "",
                "vehicle_type": "",
                "days": "",
                "slr": ""
            }

    # ── City Vendor Search ──────────────────────────────────
    if request.method == "POST" and "search_city" in request.form:
        city = request.form.get("city", "").strip().upper()
        found = Vendor.query.filter_by(city=city).all()
        vendors_list = [v.account_name for v in found] or ["No vendors found"]

    # ── Delete Action ───────────────────────────────────────
    if action == "delete" and edit_id and edit_id.isdigit():
        idx = int(edit_id)
        if tab == "vendors":
            vendor = Vendor.query.get(idx)
            if vendor:
                db.session.delete(vendor)
                db.session.commit()
                flash(f"Vendor '{vendor.account_name}' deleted!", "success")
        elif tab == "ratecards":
            rc = RateCard.query.get(idx)
            if rc:
                db.session.delete(rc)
                db.session.commit()
                flash("Rate card deleted successfully!", "success")
        elif tab == "settings":
            group = AccountGroup.query.get(idx)
            if group:
                db.session.delete(group)
                db.session.commit()
                flash(f"Account Group '{group.group_name}' deleted!", "success")
        return redirect(url_for("admin", tab=tab))

    # ── Vendors CRUD ────────────────────────────────────────
    vendor = None
    if tab == "vendors":
        if request.method == "POST" and "save_vendor" in request.form:
            account_group_id = request.form.get("account_group_id")
            account_group_name = None

            if account_group_id:
                group = AccountGroup.query.get(int(account_group_id))
                if group:
                    account_group_name = group.group_name

            data = {
                "account_name": request.form.get("account_name", ""),
                "account_group": account_group_name,
                "email": request.form.get("email", ""),
                "mobile": request.form.get("mobile", ""),
                "alt_mobile": request.form.get("alt_mobile", ""),
                "address1": request.form.get("address1", ""),
                "address2": request.form.get("address2", ""),
                "city": request.form.get("city", "").upper(),
                "state": request.form.get("state", "").upper(),
                "pin": request.form.get("pin", ""),
                "gst": request.form.get("gst", ""),
                "pan": request.form.get("pan", ""),
                "aadhaar": request.form.get("aadhaar", ""),
                "remark": request.form.get("remark", "")
            }

            vendor_id = request.form.get("vendor_id")

            if vendor_id:
                vendor = Vendor.query.get(int(vendor_id))
                if vendor:
                    for k, v in data.items():
                        setattr(vendor, k, v)
                    db.session.commit()
                    flash("Vendor updated successfully!", "success")
                else:
                    flash("Vendor not found!", "error")

            elif action == "edit" and edit_id:
                vendor = Vendor.query.get(int(edit_id))
                if vendor:
                    for k, v in data.items():
                        setattr(vendor, k, v)
                    db.session.commit()
                    flash("Vendor updated successfully!", "success")
                else:
                    flash("Vendor not found!", "error")

            else:
                new_vendor = Vendor(**data)
                db.session.add(new_vendor)
                db.session.commit()
                flash("Vendor added successfully!", "success")

            return redirect(url_for("admin", tab="vendors"))

        if action == "edit" and edit_id:
            vendor = Vendor.query.get(int(edit_id))

    # ── Rate Cards CRUD ─────────────────────────────────────
    ratecard = None
    if tab == "ratecards":
        if request.method == "POST" and "save_ratecard" in request.form:
            data = {
                "train_no": request.form.get("train_no", "").strip(),
                "vehicle_type": request.form.get("vehicle_type", ""),
                "weight_capacity": request.form.get("weight_capacity", ""),
                "parcel_type": request.form.get("parcel_type", ""),
                "days": request.form.get("days", ""),
                "origin_station": request.form.get("origin_station", "").upper(),
                "origin_code": request.form.get("origin_code", "").upper(),
                "dest_station": request.form.get("dest_station", "").upper(),
                "dest_code": request.form.get("dest_code", "").upper(),
                "rate_type": request.form.get("rate_type", ""),
                "rate_card": request.form.get("rate_card", ""),
                "vendor_id": request.form.get("vendor_id"),
                "origin_person": request.form.get("origin_person", ""),
                "origin_mobile": request.form.get("origin_mobile", ""),
                "dest_person": request.form.get("dest_person", ""),
                "dest_mobile": request.form.get("dest_mobile", ""),
                "remark": request.form.get("remark", "")
            }

            if action == "edit" and edit_id:
                rc = RateCard.query.get(int(edit_id))
                if rc:
                    for k, v in data.items():
                        setattr(rc, k, v)
                    db.session.commit()
                    message = "Rate card updated successfully!"
            else:
                new_rc = RateCard(**data)
                db.session.add(new_rc)
                db.session.commit()
                message = "Rate card added successfully!"

            return redirect(url_for("admin", tab="ratecards"))

        if action in ["add", "edit"] and edit_id:
            ratecard = RateCard.query.get(int(edit_id))

    # ── Settings (Account Groups) ───────────────────────────
    group = None
    if tab == "settings":
        if request.method == "POST" and "save_group" in request.form:
            group_name = request.form.get("group_name", "").strip()
            remark = request.form.get("remark", "")

            if not group_name:
                flash("Group name is required", "error")
            else:
                existing = AccountGroup.query.filter_by(group_name=group_name).first()
                if existing and (not edit_id or int(edit_id) != existing.sr_no):
                    flash("This group name already exists", "error")
                else:
                    if action == "edit" and edit_id:
                        group = AccountGroup.query.get(int(edit_id))
                        if group:
                            group.group_name = group_name
                            group.remark = remark
                            db.session.commit()
                            message = "Account group updated successfully!"
                    else:
                        new_group = AccountGroup(group_name=group_name, remark=remark)
                        db.session.add(new_group)
                        db.session.commit()
                        message = "Account group added successfully!"

            return redirect(url_for("admin", tab="settings"))

        if action == "edit" and edit_id:
            group = AccountGroup.query.get(int(edit_id))

    # ── Data for template ───────────────────────────────────
    vendors = Vendor.query.order_by(Vendor.account_name).all()
    ratecards = RateCard.query.all()
    account_groups = AccountGroup.query.order_by(AccountGroup.group_name).all()

    # Unique origin stations for admin search tab dropdown
    origin_stations = sorted(set(
        rc.origin_station for rc in RateCard.query.with_entities(RateCard.origin_station).distinct().all()
        if rc.origin_station
    ))

    return render_template(
        "admin.html",
        tab=tab,
        action=action,
        edit_id=edit_id,
        vendors=vendors,
        ratecards=ratecards,
        account_groups=account_groups,
        rate_result=rate_result,
        vendors_list=vendors_list,
        message=message,
        origin_stations=origin_stations,
        vendor=vendor if tab == "vendors" and action in ["add", "edit"] else None,
        ratecard=ratecard if tab == "ratecards" and action in ["add", "edit"] else None,
        group=group if tab == "settings" and action == "edit" else None
    )


# ────────────────────────────────────────────────
# LOGOUT
# ────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("user_id", None)
    return redirect(url_for("login"))



@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js',
                               mimetype='application/javascript')


# ────────────────────────────────────────────────
# Run the app (Railway / production friendly)
# ────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)




