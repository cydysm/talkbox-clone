from django.db import migrations, models


def copy_about_into_sitemeta(apps, schema_editor):
    """把 SiteAbout 的简介文本迁入 SiteMeta.about，之后移除 SiteAbout。"""
    SiteAbout = apps.get_model("blog", "SiteAbout")
    SiteMeta = apps.get_model("blog", "SiteMeta")
    about = ""
    setting = SiteAbout.objects.first()
    if setting and setting.text:
        about = setting.text
    meta = SiteMeta.objects.first()
    if meta is None:
        SiteMeta.objects.create(about=about)
        return
    if about:
        meta.about = about
        meta.save(update_fields=["about", "updated_at"])


def restore_siteabout_from_sitemeta(apps, schema_editor):
    SiteAbout = apps.get_model("blog", "SiteAbout")
    SiteMeta = apps.get_model("blog", "SiteMeta")
    meta = SiteMeta.objects.first()
    SiteAbout.objects.create(text=meta.about if meta else "")


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0015_sitemeta_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitemeta",
            name="about",
            field=models.CharField(
                blank=True,
                default="",
                help_text="显示在主页顶部，最长 200 字；留空时使用站点描述。",
                max_length=200,
                verbose_name="主页简介",
            ),
        ),
        migrations.RunPython(copy_about_into_sitemeta, restore_siteabout_from_sitemeta),
        migrations.DeleteModel(name="SiteAbout"),
    ]
