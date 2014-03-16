# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Restaurant_Holiday'
        db.delete_table(u'api_restaurant_holiday')

        # Adding model 'RestaurantOpenHours'
        db.create_table(u'api_restaurantopenhours', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('restaurant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['api.Restaurant'])),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'api', ['RestaurantOpenHours'])

        # Adding model 'RestaurantHoliday'
        db.create_table(u'api_restaurantholiday', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('restaurant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['api.Restaurant'])),
            ('closed_date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal(u'api', ['RestaurantHoliday'])

        # Adding model 'Location'
        db.create_table(u'api_location', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('timezone', self.gf('timezone_field.fields.TimeZoneField')()),
        ))
        db.send_create_signal(u'api', ['Location'])

        # Deleting field 'Restaurant.closed_every_other_weekend_initial_weekend'
        db.delete_column(u'api_restaurant', 'closed_every_other_weekend_initial_weekend')

        # Adding field 'Restaurant.closed_every_other_weekend_initial_weekend_sat'
        db.add_column(u'api_restaurant', 'closed_every_other_weekend_initial_weekend_sat',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)


        # Renaming column for 'Restaurant.location' to match new field type.
        db.rename_column(u'api_restaurant', 'location', 'location_id')
        # Changing field 'Restaurant.location'
        db.alter_column(u'api_restaurant', 'location_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['api.Location']))
        # Adding index on 'Restaurant', fields ['location']
        db.create_index(u'api_restaurant', ['location_id'])


    def backwards(self, orm):
        # Removing index on 'Restaurant', fields ['location']
        db.delete_index(u'api_restaurant', ['location_id'])

        # Adding model 'Restaurant_Holiday'
        db.create_table(u'api_restaurant_holiday', (
            ('closed_date', self.gf('django.db.models.fields.DateTimeField')()),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('restaurant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['api.Restaurant'])),
        ))
        db.send_create_signal(u'api', ['Restaurant_Holiday'])

        # Deleting model 'RestaurantOpenHours'
        db.delete_table(u'api_restaurantopenhours')

        # Deleting model 'RestaurantHoliday'
        db.delete_table(u'api_restaurantholiday')

        # Deleting model 'Location'
        db.delete_table(u'api_location')

        # Adding field 'Restaurant.closed_every_other_weekend_initial_weekend'
        db.add_column(u'api_restaurant', 'closed_every_other_weekend_initial_weekend',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Deleting field 'Restaurant.closed_every_other_weekend_initial_weekend_sat'
        db.delete_column(u'api_restaurant', 'closed_every_other_weekend_initial_weekend_sat')


        # Renaming column for 'Restaurant.location' to match new field type.
        db.rename_column(u'api_restaurant', 'location_id', 'location')
        # Changing field 'Restaurant.location'
        db.alter_column(u'api_restaurant', 'location', self.gf('django.db.models.fields.IntegerField')())

    models = {
        u'api.closedreasonmsg': {
            'Meta': {'object_name': 'ClosedReasonMsg'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msg': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'api.configuration': {
            'Meta': {'object_name': 'Configuration'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'unit_test_mode': ('django.db.models.fields.BooleanField', [], {})
        },
        u'api.gcmregistrationid': {
            'Meta': {'object_name': 'GCMRegistrationId'},
            'gcm_registration_id': ('django.db.models.fields.CharField', [], {'max_length': '600'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'api.location': {
            'Meta': {'object_name': 'Location'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'timezone': ('timezone_field.fields.TimeZoneField', [], {})
        },
        u'api.meal': {
            'Meta': {'object_name': 'Meal'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meal_category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.MealCategory']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '85'}),
            'pic_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'price': ('django.db.models.fields.IntegerField', [], {}),
            'restaurant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Restaurant']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'api.mealcategory': {
            'Meta': {'object_name': 'MealCategory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '85'})
        },
        u'api.mealrecommendation': {
            'Meta': {'object_name': 'MealRecommendation'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meal': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Meal']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'api.order': {
            'Meta': {'object_name': 'Order'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pos_slip_number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'restaurant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Restaurant']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'user_comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'vendor_comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'api.orderitem': {
            'Meta': {'object_name': 'OrderItem'},
            'amount': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meal': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Meal']"}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Order']"})
        },
        u'api.profile': {
            'Meta': {'object_name': 'Profile'},
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'failure': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'pic_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'restaurant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Restaurant']", 'null': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'api.restaurant': {
            'Meta': {'object_name': 'Restaurant'},
            'capacity': ('django.db.models.fields.IntegerField', [], {'default': '99'}),
            'closed_every_other_weekend_initial_weekend_sat': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'closed_reason': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.ClosedReasonMsg']", 'null': 'True'}),
            'closed_rule': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'current_number_slip': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Location']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '33'}),
            'number_slip': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'pic_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'api.restaurantholiday': {
            'Meta': {'object_name': 'RestaurantHoliday'},
            'closed_date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restaurant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Restaurant']"})
        },
        u'api.restaurantopenhours': {
            'Meta': {'object_name': 'RestaurantOpenHours'},
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restaurant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Restaurant']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'api.userregistration': {
            'Meta': {'object_name': 'UserRegistration'},
            'clicked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'code': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'ctime': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['api']