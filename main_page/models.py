from django.db import models


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
    source_link = models.CharField(max_length=200)
    soucer_description = models.CharField(max_length=1000)
    #source_type = models.CharField(max_length=200)
    source_type = models.CharField(choices=SOURCE_ORIGIN, max_length=50)
    pub_date = models.DateField('date published')

    def __str__(self):
        return self.source_name

class SnippetCode(models.Model):
    snippet_code_name = models.CharField(max_length=100)
    snippet_code = models.TextField(max_length=10000)
    snippet_code_type = models.CharField(choices=SNIPPET_CODE_TYPE, max_length=50)

    def __str__(self):
        return self.snippet_code_name

class GeonetworkMetadata(models.Model):
    uuid = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    abstract = models.TextField(max_length=10000)
    category = models.CharField(max_length=100)
    keyword = models.CharField(max_length=500)
    image = models.CharField(max_length=500)
    geom = models.
    
    def __str__(self):
        return self.title