"""Unmanaged Django mapping of the Base gallery physical subset."""
from django.db import models


class State(models.Model):
    code = models.CharField(max_length=5, primary_key=True, null=False)
    name = models.CharField(max_length=100, primary_key=False, null=True)

    class Meta:
        app_label = "gramlot_invoice"
        managed = False
        db_table = '"invc"."invc_state"'

class Customer(models.Model):
    id = models.CharField(max_length=22, primary_key=True, null=False)
    account_name = models.TextField(primary_key=False, null=True)
    suburb = models.TextField(primary_key=False, null=True)
    state = models.ForeignKey(State, on_delete=models.DO_NOTHING, db_column='state', null=True)

    class Meta:
        app_label = "gramlot_invoice"
        managed = False
        db_table = '"invc"."invc_customer"'

class Invoice(models.Model):
    id = models.CharField(max_length=22, primary_key=True, null=False)
    inv_number = models.CharField(max_length=10, primary_key=False, null=True, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, db_column='customer_id', null=True)
    date = models.DateField(primary_key=False, null=True)
    total = models.DecimalField(max_digits=14, decimal_places=2, primary_key=False, null=True)

    class Meta:
        app_label = "gramlot_invoice"
        managed = False
        db_table = '"invc"."invc_invoice"'

class Product(models.Model):
    id = models.CharField(max_length=22, primary_key=True, null=False)
    code = models.CharField(max_length=10, primary_key=False, null=True)
    description = models.CharField(max_length=80, primary_key=False, null=True)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, primary_key=False, null=True)

    class Meta:
        app_label = "gramlot_invoice"
        managed = False
        db_table = '"invc"."invc_product"'

class InvoiceRow(models.Model):
    id = models.CharField(max_length=22, primary_key=True, null=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.DO_NOTHING, db_column='invoice_id', null=True)
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, db_column='product_id', null=True)
    quantity = models.IntegerField(primary_key=False, null=True)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, primary_key=False, null=True)
    tot_price = models.DecimalField(max_digits=14, decimal_places=2, primary_key=False, null=True)

    class Meta:
        app_label = "gramlot_invoice"
        managed = False
        db_table = '"invc"."invc_invoice_row"'
