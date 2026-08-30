from django.db import migrations


def seed_share_targets(apps, schema_editor):
    from apps.blog.share_targets import DEFAULT_ORDER

    ShareTarget = apps.get_model("blog", "ShareTarget")
    for index, name in enumerate(DEFAULT_ORDER):
        ShareTarget.objects.get_or_create(
            name=name, defaults={"order": index, "is_visible": True}
        )


def unseed_share_targets(apps, schema_editor):
    ShareTarget = apps.get_model("blog", "ShareTarget")
    ShareTarget.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0008_sharetarget"),
    ]

    operations = [
        migrations.RunPython(seed_share_targets, unseed_share_targets),
    ]
