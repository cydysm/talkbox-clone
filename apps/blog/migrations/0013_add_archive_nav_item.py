from django.db import migrations


def add_archive_nav_item(apps, schema_editor):
    NavItem = apps.get_model("blog", "NavItem")
    NavItem.objects.get_or_create(
        title="存档",
        url="/archive/",
        defaults={"order": 5, "visibility": "all", "show_in_post_header": True},
    )


def remove_archive_nav_item(apps, schema_editor):
    NavItem = apps.get_model("blog", "NavItem")
    NavItem.objects.filter(title="存档", url="/archive/").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0012_navitem_show_in_post_header'),
    ]

    operations = [
        migrations.RunPython(add_archive_nav_item, remove_archive_nav_item),
    ]
