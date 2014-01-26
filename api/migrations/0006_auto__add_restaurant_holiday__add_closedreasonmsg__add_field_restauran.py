# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Restaurant_Holiday'
        db.create_table(u'api_restaurant_holiday', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('restaurant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['api.Restaurant'])),
            ('closed_date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'api', ['Restaurant_Holiday'])

        # Adding model 'ClosedReasonMsg'
        db.create_table(u'api_closedreasonmsg', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('msg', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'api', ['ClosedReasonMsg'])

        # Adding field 'Restaurant.closed_reason'
        db.add_column(u'api_restaurant', 'closed_reason',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['api.ClosedReasonMsg'], null=True),
                      keep_default=False)

        # Adding field 'Restaurant.closed_rule'
        db.add_column(u'api_restaurant', 'closed_rule',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Restaurant.closed_every_other_weekend_initial_weekend'
        db.add_column(u'api_restaurant', 'closed_every_other_weekend_initial_weekend',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'Restaurant_Holiday'
        db.delete_table(u'api_restaurant_holiday')

        # Deleting model 'ClosedReasonMsg'
        db.delete_table(u'api_closedreasonmsg')

        # Deleting field 'Restaurant.closed_reason'
        db.delete_column(u'api_restaurant', 'closed_reason_id')

        # Deleting field 'Restaurant.closed_rule'
        db.delete_column(u'api_restaurant', 'closed_rule')

        # Deleting field 'Restaurant.closed_every_other_weekend_initial_weekend'
        db.delete_column(u'api_restaurant', 'closed_every_other_weekend_initial_weekend')


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
            'closed_every_other_weekend_initial_weekend': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'closed_reason': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.ClosedReasonMsg']", 'null': 'True'}),
            'closed_rule': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'current_number_slip': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '33'}),
            'number_slip': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'pic_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'api.restaurant_holiday': {
            'Meta': {'object_name': 'Restaurant_Holiday'},
            'closed_date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'restaurant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['api.Restaurant']"})
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