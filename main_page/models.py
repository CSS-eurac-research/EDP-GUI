from django.db import models
from django.contrib.gis.db import models
from django.contrib import admin
from datetime import date

SOURCE_ORIGIN = (
            ('Gitlab','Gitlab'),
            ('Github','Github'),
            ('ReadTheDocs','ReadTheDocs'),
            ('Other','Other'),
            )

SNIPPET_CODE_TYPE = (
            ('openEO','openEO'),
            ('InfluxDB','InfluxDB'),
            ('python','python'),
            ('Java','Java'),
            )

class DocSource(models.Model):
    source_name = models.CharField(max_length=100)
    source_link = models.CharField(max_length=200, null=True)
    source_description = models.CharField(max_length=1000, null=True)
    #source_type = models.CharField(max_length=200)
    # source_type = models.CharField(choices=SOURCE_ORIGIN, max_length=50, null=True)
    source_category = models.CharField(max_length=200, null=True)
    pub_date = models.DateField('date published')

    def __str__(self):
        return self.source_name

class SnippetCode(models.Model):
    snippet_code_name = models.CharField(max_length=100)
    snippet_code = models.TextField(max_length=10000, null=True)
    # snippet_code_type = models.CharField(choices=SNIPPET_CODE_TYPE, max_length=50)
    snippet_category = models.CharField(max_length=200, default="No category")
    snippet_programming_language = models.CharField(max_length=200, default="No programming language")

    def __str__(self):
        return self.snippet_code_name

class GeonetworkMetadata(models.Model):
    uuid = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=500, null=True, default="No title")
    abstract = models.TextField(max_length=10000, null=True)
    category = models.CharField(max_length=500, null=True)
    keyword = models.CharField(max_length=1000, null=True)
    thumbnail = models.CharField(max_length=1000, null=True)
    geom = models.PolygonField(srid=4326, null=True)
    last_update = models.DateTimeField(null=True, editable=False)
    period_begin = models.DateTimeField(null=True)
    period_end = models.DateTimeField(null=True)
    doi = models.CharField(max_length=500, null=True)
    citation = models.TextField(max_length=10000, null=True)
    name_collection = models.CharField(max_length=500, null=True)
    cl_topic = models.CharField(max_length=500, null=True)
    presentation_form = models.CharField(max_length=500, null=True)
    supplemental_information = models.TextField(max_length=10000, null=True)

    def __str__(self):
        return self.title


class FairScore(models.Model):
    uuid = models.CharField(max_length=100, primary_key=True)
    object_identifier = models.CharField(max_length=500, null=True)
    score_overall = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    score_f = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    score_a = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    score_i = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    score_r = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    earned_f = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    earned_a = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    earned_i = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    earned_r = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    total_f = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    total_a = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    total_i = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    total_r = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    maturity_f = models.SmallIntegerField(null=True)
    maturity_a = models.SmallIntegerField(null=True)
    maturity_i = models.SmallIntegerField(null=True)
    maturity_r = models.SmallIntegerField(null=True)
    maturity_overall = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    metric_version = models.CharField(max_length=20, null=True)
    fuji_test_id = models.CharField(max_length=100, null=True)
    assessed_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)
    full_result = models.JSONField(null=True)

    class Meta:
        managed = False
        db_table = "main_page_fairscore"

    def __str__(self):
        return self.uuid

