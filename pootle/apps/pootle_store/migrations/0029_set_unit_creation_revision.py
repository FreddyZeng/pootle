# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-23 10:20
from __future__ import unicode_literals

import logging

from django.conf import settings
from django.db import migrations

from pootle.core.batch import Batch
from pootle_store.constants import OBSOLETE


logger = logging.getLogger(__name__)


SET_CREATION_REVISION_SQL = (
    "UPDATE `pootle_store_unit_source` "
    "  JOIN `pootle_store_unit` "
    "    ON `pootle_store_unit`.`id` = `pootle_store_unit_source`.`unit_id` "
    "  LEFT JOIN `pootle_store_unit_change` "
    "    ON `pootle_store_unit`.`id` = `pootle_store_unit_change`.`unit_id` "
    "  LEFT JOIN `pootle_app_submission` "
    "    ON `pootle_store_unit`.`id` = `pootle_app_submission`.`unit_id` "
    "  SET `pootle_store_unit_source`.`creation_revision` = `pootle_store_unit`.`revision` "
    "   WHERE `pootle_app_submission`.`id` IS NULL "
    "     AND `pootle_store_unit_change`.id IS NULL "
    "     AND `pootle_store_unit`.`state` >= 0 "
    "     AND `pootle_store_unit`.`revision` > 0")


def set_creation_revisions_with_sql(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    result = cursor.execute(SET_CREATION_REVISION_SQL)
    logger.debug("Updated %s for unit_source.creation_revision" % result)


def set_creation_revisions_with_orm(apps, schema_editor):
    UnitSource = apps.get_model("pootle_store.UnitSource")
    no_change = UnitSource.objects.filter(unit__submission__isnull=True).filter(unit__change__isnull=True)
    no_change = no_change.exclude(unit__state=OBSOLETE).filter(unit__revision__gt=0)
    no_change = list(no_change.select_related("unit").only("unit__revision"))

    def _set_creation_revision(unit_source):
        unit_source.creation_revision = unit_source.unit.revision
        return unit_source
    Batch(UnitSource.objects, batch_size=1000).update(
        no_change,
        update_method=_set_creation_revision,
        update_fields=["creation_revision"],
        reduces=False)


def set_creation_revisions(apps, schema_editor):
    if schema_editor.connection.vendor == "mysql" and settings.POOTLE_SQL_MIGRATIONS:
        set_creation_revisions_with_sql(apps, schema_editor)
    else:
        set_creation_revisions_with_orm(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0028_unitsource_creation_revision'),
    ]

    operations = [
        migrations.RunPython(set_creation_revisions),
    ]