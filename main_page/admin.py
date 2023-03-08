from django.contrib import admin
from .models import DocSource, SnippetCode, GeonetworkMetadata
import psycopg2
import requests
from datetime import datetime
from django.contrib.admin import AdminSite

#@admin.action(description='Download all the metadata from the Geonetwork catalaog')
def download_all_metadata(modelAdmin, request, queryset):
    conn = psycopg2.connect(
       database="edp_portal_gui", user='edp_gui_user', password='73bd357832012a62357095bf6d9324f8', host='10.8.244.39',
       port='5432'
    )
    try:
        step = 1
        current_collection = []
        results = requests.get("http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&summaryOnly=1")
        # print(results.json())
        summary_results = results.json()
        # print(summary_results)
        total_number_metadata = summary_results[0]['@count']
        metadata_title_item_list = []
        # print(total_number_metadata)
        number_loop = int(int(total_number_metadata) / 100)
        print(str(step) + ". Download metadata from Geonetwork")
        step = step + 1
        if int(total_number_metadata) % 100 > 0:
            for k in range(number_loop + 1):
                url_first_part = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&bucket=s101&facet.q=&fast=index&from=" + str(
                    (100 * k) + 1)
                url_end_part = "&resultType=details&sortBy=title&sortOrder=reverse&to=" + str((k + 1) * 100)
                final_url = url_first_part + url_end_part
                # print(final_url)
                results = requests.get(final_url)
                current_results = results.json()
                current_collection = current_collection + current_results['metadata']
        print(str(step) + ". Metadata downloaded")
        step = step + 1
        # print((current_collection))

        metadata = []

        print(str(step) + ". Set up of metadata")
        step = step + 1

        for item in current_collection:
            # print(item)
            attributes = {}
            if "uuid" in item["geonet:info"]:
                uuid = item["geonet:info"]["uuid"]
                attributes["uuid"] = item["geonet:info"]["uuid"]
                # attributes.append("uuid")
                title = abstract = category = keyword = thumbnail = polygon = ""

                if "title" in item:
                    attributes["title"] = item["title"]
                    title = item["title"].replace("\'", "\"")
                if "abstract" in item:
                    attributes["abstract"] = item["abstract"]
                    abstract = item["abstract"]
                if "category" in item:
                    attributes["category"] = item["category"]
                    category = item["category"].replace("\'", "\"")
                if "keyword" in item:
                    attributes["keyword"] = item["keyword"]
                    keyword = ",".join(item["keyword"]).replace("\'", "\"")
                if "image" in item:
                    thumbnail = item["image"].split("|")
                    attributes["thumbnail"] = thumbnail[1]
                if "geoBox" in item:
                    # QUERY WITH GEOM POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))
                    # print(item["geoBox"])
                    coords = (item["geoBox"].split("|"))
                    # print(len(coords))
                    polygon = "ST_MakeEnvelope(" + ",".join(coords) + ", 4326)"
                    attributes["geom"] = polygon

                metadata.append(attributes)

        print(str(step) + ". Set up query")
        step = step + 1

        tmp_values = []
        queries = []
        for i in metadata:
            # print(i)
            if "uuid" in i:
                queries.append("INSERT INTO main_page_geonetworkmetadata (uuid) VALUES (\'" + i["uuid"] + "\') ON CONFLICT ON CONSTRAINT main_page_geonetworkmetadata_uuid_f4dac5b9_uniq DO NOTHING;")
                if "title" in i:
                    # queries.append("INSERT INTO main_page_geonetworkmetadata (title) VALUES (\"" + i["title"] + "\") WHERE uuid == \"" + i["uuid"] + "\"")
                    queries.append(
                        "UPDATE main_page_geonetworkmetadata SET title = \'" + i["title"] + "\' WHERE uuid = \'" + i[
                            "uuid"] + "\'")
                if "abstract" in i:
                    # queries.append("INSERT INTO main_page_geonetworkmetadata (abstract) VALUES (\"" + i["abstract"] + "\") WHERE uuid == \"" + i["uuid"] + "\"")
                    queries.append("UPDATE main_page_geonetworkmetadata SET abstract = \'" + i["abstract"].replace("\'",
                                                                                                                   "\"") + "\' WHERE uuid = \'" +
                                   i["uuid"] + "\'")
                if "category" in i:
                    # queries.append("INSERT INTO main_page_geonetworkmetadata (category) VALUES (\"" + i["category"] + "\") WHERE uuid == \"" + i["uuid"] + "\"")
                    queries.append(
                        "UPDATE main_page_geonetworkmetadata SET category = \'" + i["category"] + "\' WHERE uuid = \'" + i[
                            "uuid"] + "\'")
                if "keyword" in i:
                    # queries.append("INSERT INTO main_page_geonetworkmetadata (keyword) VALUES (\"" + ",".join(i["keyword"]) + "\") WHERE uuid == \"" + i["uuid"] + "\"")
                    queries.append("UPDATE main_page_geonetworkmetadata SET keyword = \'" + ",".join(
                        i["keyword"]) + "\' WHERE uuid = \'" + i["uuid"] + "\'")
                if "thumbnail" in i:
                    # queries.append("INSERT INTO main_page_geonetworkmetadata (image) VALUES (\"" + i["thumbnail"] + "\") WHERE uuid == \"" + i["uuid"] + "\"")
                    queries.append(
                        "UPDATE main_page_geonetworkmetadata SET thumbnail = \'" + i["thumbnail"] + "\' WHERE uuid = \'" +
                        i["uuid"] + "\'")
                if "geom" in i:
                    # queries.append("INSERT INTO main_page_geonetworkmetadata (geom) VALUES (" + i["geom"] + ") WHERE uuid == \"" + i["uuid"] + "\"")
                    queries.append("UPDATE main_page_geonetworkmetadata SET geom = " + i["geom"] + " WHERE uuid = \'" + i[
                        "uuid"] + "\'")
                    # print("UPDATE main_page_geonetworkmetadata SET geom = " + i["geom"] + " WHERE uuid = \'" + i["uuid"] + "\'")

                queries.append("UPDATE main_page_geonetworkmetadata SET last_update = \'" + str(datetime.now()) + "\' WHERE uuid = \'" + i[
                   "uuid"] + "\'")

            else:
                print(str(step) + ". No uuid found, pass to the next metadata.")
                step = step + 1

        # print(";\n".join(queries))
        final_query = ";".join(queries) + ";"
        # print(final_query)
        print(str(step) + ". Query composed and ready to be executed")
        step = step + 1

        cursor = conn.cursor()
        cursor.execute(final_query)
        print(str(step) + ". Query executed correctly")
        step = step + 1
        conn.commit()
        print(str(step) + ". Commit on the database completed")
        step = step + 1
        cursor.close()
    except Exception as error:
        print("-------------------------------------------------------------------------")
        print("ERROR")
        print(error)
        print("-------------------------------------------------------------------------")
    finally:
        conn.close()
        print(str(step) + ". Connection to the database closed")

class GeonetworkMetadataAdmin(admin.ModelAdmin):
    list_display = ['title', 'uuid', 'category', 'last_update']
    search_fields = ['title', 'uuid', 'category', 'keyword', 'abstract']
    readonly_fields=('doi','citation', 'supplemental_information')
    list_filter = ['category']
    actions = [download_all_metadata]

class SnippetCodeAdmin(admin.ModelAdmin):
    list_display = ['snippet_code_name', 'snippet_code', 'snippet_category', 'snippet_programming_language']
    search_fields = ['snippet_code_name', 'snippet_code', 'snippet_category',  'snippet_programming_language']
    list_filter = ['snippet_category']

class DocSourceAdmin(admin.ModelAdmin):
    list_display = ['source_name', 'source_category', 'source_description']
    search_fields = ['source_name', 'source_category', 'source_description']
    list_filter = ['source_category']


class MyAdminSite(AdminSite):
    site_header = 'EDP Django administration'

#admin.site = MyAdminSite(name='admin')
admin.site.register(DocSource, DocSourceAdmin)
admin.site.register(SnippetCode, SnippetCodeAdmin)
admin.site.register(GeonetworkMetadata, GeonetworkMetadataAdmin)


