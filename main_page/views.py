from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.http import JsonResponse
import requests
import json 
import ast, re
import psycopg2
from .models import DocSource, SnippetCode, GeonetworkMetadata


class DocsPageView(generic.ListView):
    template_name = 'docs.html'
    context_object_name = 'latest_docs_sources_list'

    def get_queryset(self):
        """Return the last five published docs sources."""
        return DocSource.objects.all()
    #model = DocSource
    #return render(request, 'docs.html', {})

def main_page(request):
    return render(request, 'main_page.html', {})

def discovery(request):
    title_list = "no title found"
    #category_list = "no category found"
    category_list = ["no category found"]
    try:
        print(request.GET)
        conn = psycopg2.connect(
                database="edp_portal_gui", user='edp_gui_user', password='73bd357832012a62357095bf6d9324f8', host='10.8.244.39', port='5432'
            )
        cursor = conn.cursor()
        tmp_category_list = GeonetworkMetadata.objects.values_list('category', flat=True)
        category_list = []
        for c in tmp_category_list:
            if c not in category_list and c != None:
                category_list.append(c)
        
        title_list = ""

        where_clause_array = []
        where_clause_array.append("all")
        if request.GET.get('categories'):
            cateogories_selected = request.GET.get('categories')
            if "all" not in cateogories_selected:
                #print("CATEGORIES " + cateogories_selected)                
                #print(cateogories_selected.split(","))
                where_clause_array.remove("all")
                for c in cateogories_selected.split(","):
                    where_clause_array.append("category='"+c+"'")
            else:
                where_clause_array.append("all")
        
        #if 'term' in request.GET:  
        #print(request.GET.get("term"))
        #searchKeyword = request.GET.get("term")
        #category_query = "SELECT DISTINCT(category) FROM main_page_geonetworkmetadata mpg WHERE category ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%'"
        category_query = "SELECT DISTINCT(category) FROM main_page_geonetworkmetadata mpg"
        cursor.execute(category_query)
        results = cursor.fetchall()
        for i in results:
            if i[0]:
                #title_list.append(i[0].replace("\"","")) 
                title_list = title_list + "," +i[0]
        #keyword_query = "SELECT DISTINCT(keyword) FROM main_page_geonetworkmetadata mpg WHERE keyword ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%'"
        keyword_query = "SELECT DISTINCT(keyword) FROM main_page_geonetworkmetadata mpg"
        cursor.execute(keyword_query)
        results = cursor.fetchall()
        for i in results:
            if i[0]:
                #title_list.append(i[0].replace("\"","")) 
                keyword_list = i[0].split(",")
                for keyword in keyword_list:
                    if keyword not in title_list: 
                        title_list = title_list + "," + keyword
        #print(title_list)
        #title_query = "SELECT title FROM main_page_geonetworkmetadata mpg WHERE title ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%'"
        title_query = "SELECT title FROM main_page_geonetworkmetadata mpg"
        cursor.execute(title_query)
        results = cursor.fetchall()
        for i in results:
            if i[0]:
                #title_list.append(i[0].replace("\"","")) 
                title_list = title_list + "," +i[0]
        #print(len(title_list))
        #if (len(title_list) == 0):
        if (title_list == ""):
            title_list = "no title found"    
        #    return JsonResponse(title_list, safe=False, status=200)
        if request.GET.get('period_begin') and request.GET.get('period_end') and request.GET.get('box') and request.GET.get('search'):
            period_begin = request.GET.get('period_begin')
            period_end = request.GET.get('period_end')
            #print(period_begin + " " + period_end)
            searchKeyword = request.GET.get('search')
            boundingbox = request.GET.get('box')
            boundingbox = boundingbox.split(",")
            #print(boundingbox)
            polygon = ""
            for i in range(len(boundingbox)):
                if i == 0:
                    polygon = polygon + boundingbox[i]
                else:
                    if i % 2 == 0:
                        polygon = polygon + "," + boundingbox[i]
                    elif i%2 != 0:
                        polygon = polygon + " " + boundingbox[i]
            
            polygon = "POLYGON((" + polygon + "))"

            if "all" not in where_clause_array:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            else:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' ORDER BY title ASC"

            #final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, period_begin, period_end FROM main_page_geonetworkmetadata WHERE date_trunc('day', period_begin) >= '"+period_begin+"' AND date_trunc('day', period_end) <= '"+period_end+"' ORDER BY title ASC;"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('period_begin') and request.GET.get('period_end') and request.GET.get('box'):
            period_begin = request.GET.get('period_begin')
            period_end = request.GET.get('period_end')
            #print(period_begin + " " + period_end)
            boundingbox = request.GET.get('box')
            boundingbox = boundingbox.split(",")
            #print(boundingbox)
            polygon = ""
            for i in range(len(boundingbox)):
                if i == 0:
                    polygon = polygon + boundingbox[i]
                else:
                    if i % 2 == 0:
                        polygon = polygon + "," + boundingbox[i]
                    elif i%2 != 0:
                        polygon = polygon + " " + boundingbox[i]
            #print(polygon)
            polygon = "POLYGON((" + polygon + "))"   

            if "all" not in where_clause_array:         
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            else:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' ORDER BY title ASC"
            #final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, period_begin, period_end FROM main_page_geonetworkmetadata WHERE date_trunc('day', period_begin) >= '"+period_begin+"' AND date_trunc('day', period_end) <= '"+period_end+"' ORDER BY title ASC;"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('period_begin') and request.GET.get('period_end') and request.GET.get('search'):
            period_begin = request.GET.get('period_begin')
            period_end = request.GET.get('period_end')
            #print(period_begin + " " + period_end)
            searchKeyword = request.GET.get('search')
            #print("KEYWORD " + searchKeyword)
            if "all" not in where_clause_array:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            else:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' ORDER BY title ASC"

            #final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, period_begin, period_end FROM main_page_geonetworkmetadata WHERE date_trunc('day', period_begin) >= '"+period_begin+"' AND date_trunc('day', period_end) <= '"+period_end+"' ORDER BY title ASC;"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('box') and request.GET.get('search'):
            searchKeyword = request.GET.get('search')
            boundingbox = request.GET.get('box')
            boundingbox = boundingbox.split(",")
            #print(boundingbox)
            polygon = ""
            for i in range(len(boundingbox)):
                if i == 0:
                    polygon = polygon + boundingbox[i]
                else:
                    if i % 2 == 0:
                        polygon = polygon + "," + boundingbox[i]
                    elif i%2 != 0:
                        polygon = polygon + " " + boundingbox[i]
            
            polygon = "POLYGON((" + polygon + "))"  
            #print(polygon)
            #print("KEYWORD " + searchKeyword + " BBOX " + boundingbox)
            if "all" not in where_clause_array:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            else:            
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' ORDER BY title ASC"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('period_begin') and request.GET.get('period_end'):
            period_begin = request.GET.get('period_begin')
            period_end = request.GET.get('period_end')
            #print(period_begin + " " + period_end)
            if "all" not in where_clause_array:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, period_begin, period_end FROM main_page_geonetworkmetadata WHERE (date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"') AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC;"
            else:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, period_begin, period_end FROM main_page_geonetworkmetadata WHERE date_trunc('day', period_begin) BETWEEN '"+period_begin+"' AND '"+period_end+"' OR date_trunc('day', period_end) BETWEEN '"+period_begin+"' AND '"+period_end+"' ORDER BY title ASC;"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        # if request.GET.get('box'):            
        #     boundingbox = request.GET.get('box')
        #     boundingbox = boundingbox.split(",")
        #     #print(boundingbox)
        #     polygon = ""
        #     for i in range(len(boundingbox)):
        #         if i == 0:
        #             polygon = polygon + boundingbox[i]
        #         else:
        #             if i % 2 == 0:
        #                 polygon = polygon + "," + boundingbox[i]
        #             elif i%2 != 0:
        #                 polygon = polygon + " " + boundingbox[i]
        #     #print(polygon)
        #     polygon = "POLYGON((" + polygon + "))"      
        #     if "all" not in where_clause_array:
        #         final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_CONTAINS(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
        #     else:
        #         final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_CONTAINS(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) ORDER BY title ASC"
        #     print(final_query)
        #     cursor.execute(final_query)
        #     #print(conn.commit())
        #     results = cursor.fetchall()
        #     return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('box'):
            print("BOX")            
            boundingbox = request.GET.get('box')
            boundingbox = boundingbox.split(",")
            #print(boundingbox)
            polygon = ""
            for i in range(len(boundingbox)):
                if i == 0:
                    polygon = polygon + boundingbox[i]
                else:
                    if i % 2 == 0:
                        polygon = polygon + "," + boundingbox[i]
                    elif i%2 != 0:
                        polygon = polygon + " " + boundingbox[i]
            #print(polygon)
            polygon = "POLYGON((" + polygon + "))"

            print('where_clause_array')
            print(where_clause_array)
            if "all" not in where_clause_array:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            else:            
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE ST_Intersects(ST_GEOMFROMTEXT('" + polygon + "', 4326), mpg.geom) ORDER BY title ASC"
            print(final_query)
            cursor.execute(final_query)
            #print(conn.commit())
            results = cursor.fetchall()
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('search'):
            print("SEARCH")
            searchKeyword = request.GET.get('search')
            #print("KEYWORD " + searchKeyword)

            if "all" not in where_clause_array:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' AND (" + " OR ".join(where_clause_array) + ") ORDER BY title ASC"
            else:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE (title, abstract, category, keyword)::text ILIKE '%" + "%".join(searchKeyword.split(" ")) + "%' ORDER BY title ASC"
            cursor.execute(final_query)
            print(final_query)
            results = cursor.fetchall()
            #print(results)
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)
        if request.GET.get('categories'):
            print("CATEGORY")
            cateogories_selected = request.GET.get('categories')
            if "all" not in cateogories_selected:
                #print("CATEGORIES " + cateogories_selected)
                where_clause_array = []
                #print(cateogories_selected.split(","))
                for c in cateogories_selected.split(","):
                    where_clause_array.append("category='"+c+"'")

                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg WHERE " + " OR ".join(where_clause_array) + " ORDER BY title ASC"
            else:
                final_query = "SELECT uuid, title, abstract, category, keyword, thumbnail, ST_AsGeoJSON(geom) as geom, period_begin, period_end FROM main_page_geonetworkmetadata mpg ORDER BY title ASC"
            print(final_query)
            cursor.execute(final_query)
            results = cursor.fetchall()
            #print(results)
            return JsonResponse({'metadata_results': results, 'title_list': title_list, 'category_list': category_list}, safe=False, status=200)

    except GeonetworkMetadata.DoesNotExist:
        raise Http404("GeonetworkMetadata does not exist")
    #finally:
    #    metadata_list = GeonetworkMetadata.objects.all()    
    #    return render(request, 'discovery.html', {'metadata_list': metadata_list, 'title_list': title_list})
    #print("finally")
    cursor.close()
    conn.close()
    metadata_list = GeonetworkMetadata.objects.order_by('title')
    #print(title_list)    
    #print(metadata_list)
    return render(request, 'discovery.html', {'metadata_list': metadata_list, 'title_list': title_list, 'category_list': category_list})
    #return render(request, 'discovery.html', {}) 
    
def jupyter_page(request):
    return render(request, 'jupyter.html', {})

def openeo_page(request):
    return render(request, 'openeo.html', {})

def pgadmin_page(request):
    return render(request, 'pgadmin.html', {})

def maps_page(request):
    return render(request, 'maps.html', {})

def result_detail(request, uuid):
    # url = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&_draft=y+or+n+or+e&_isTemplate=y+or+n&fast=index&uuid="+uuid
    # #url = "http://edp-portal.eurac.edu/geonetwork/srv/api/0.1/records/"+uuid
    # print(url)
    # results = requests.get(url, headers = {"Accept":"application/json;charset=utf-8", "content-type": "application/json;charset=utf-8"})
    # print(results.json())
    # result_json_str = JsonResponse(results.json()).content.decode("utf-8") 
    # result_json = ast.literal_eval(result_json_str)
    metadata_details = get_metadata_details(request, uuid)
    #print(metadata_details)
    if ("error"  not in metadata_details):
    #     result_json["metadata"]["keyword"] = ", ".join(result_json["metadata"]["keyword"])
    #     result_json["metadata"]["responsibleParty"] = result_json["metadata"]["responsibleParty"][0].replace("|", " ")
        
                
        #snippet_code_list = SnippetCode.objects.filter(snippet_category__icontains=result_json["metadata"]["category"])
        #docs_list = DocSource.objects.filter(source_category__icontains=result_json["metadata"]["category"])
        snippet_code_list = SnippetCode.objects.filter(snippet_category__icontains=metadata_details["category"])
        for i in snippet_code_list:
            if 'name_collection' in metadata_details:
                i.snippet_code = i.snippet_code.replace("NAME_COLLECTION", metadata_details['name_collection'])
            if 'minLon' in metadata_details:
                i.snippet_code = i.snippet_code.replace("MIN_LON", metadata_details['minLon'])
            if 'minLat' in metadata_details:
                i.snippet_code = i.snippet_code.replace("MIN_LAT", metadata_details['minLat'])
            if 'maxLon' in metadata_details:
                i.snippet_code = i.snippet_code.replace("MAX_LON", metadata_details['maxLon'])
            if 'maxLat' in metadata_details:
                i.snippet_code = i.snippet_code.replace("MAX_LAT", metadata_details['maxLat'])
            if 'tempExtentBegin' in metadata_details and 'tempExtentEnd' in metadata_details:
                i.snippet_code = i.snippet_code.replace("TEMPORAL_EXTENT", "["+metadata_details['tempExtentBegin']+","+metadata_details['tempExtentEnd']+"]")
                i.snippet_code = i.snippet_code.replace("STARTTIME", metadata_details['tempExtentBegin'])
                i.snippet_code = i.snippet_code.replace("ENDTIME", metadata_details['tempExtentEnd'])
            if 'title' in metadata_details:
                if metadata_details['category'].lower() == 'sos':
                    title_split = metadata_details['title'].split('_')
                    foi = title_split[1]
                    observable_property = title_split[0]
                    procedure = metadata_details['title']
                    sos_url = 'http://monalisasos.eurac.edu/sos/api/v1/'
                    i.snippet_code = i.snippet_code.replace('FOI', '\"'+foi+'\"')
                    i.snippet_code = i.snippet_code.replace('OBSERVABLE_PROPERTY', '\"'+observable_property+'\"')
                    i.snippet_code = i.snippet_code.replace('PROCEDURE', '\"'+procedure+'\"')
                    i.snippet_code = i.snippet_code.replace('SOS_URL', '\"'+sos_url+'\"')

        docs_list = DocSource.objects.filter(source_category__icontains=metadata_details["category"])

        context = {
            "uuid" : uuid,
            #"result_json" : result_json["metadata"],
            "result_json" : metadata_details,
            "snippet_code_list" : snippet_code_list,
            "docs_list" : docs_list
            #'title': result_json["metadata"]["title"],
        }
        return render(request, 'result_detail.html', context)
    else:
        #print(metadata_details)
        context = {
            "error" : "No metadata found for this uuid (" + uuid + ")"
        }
        return render(request, 'result_detail.html', context)

def get_metadata_details(request, uuid):
    try:
        metadata_detail = {}
        url = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&_draft=y+or+n+or+e&_isTemplate=y+or+n&fast=index&uuid="+uuid
        print(url)
        results = requests.get(url).json()
        #print(results)
        if ("metadata" in results):
            current_metadata = results['metadata']
            if 'responsibleParty' in current_metadata:
                for i in current_metadata['responsibleParty']:
                    #print(current_metadata['responsibleParty'])
                    if 'resource' in i and 'Custodian' not in i:
                        str_splitted = i.split("|")
                        contact = email = address = ""
                        for j in range(len(str_splitted)):
                            if re.search("^[0-9]$", str_splitted[j]):
                                continue
                            if '@' in str_splitted[j]:
                                email = str_splitted[j]
                            elif j>0 and j<7 and 'resource' not in str_splitted[j]:
                                contact = contact + " " + str_splitted[j]
                            elif j>=7 and 'http' not in str_splitted[j]:
                                address = address + " " + str_splitted[j]
                        #metadata_detail['contactResource'] = { 'contactName' : contact.strip(), 'email' : email.strip(), 'address' : address.replace(" 0 ", "").replace("  0", "").strip() }
                        metadata_detail['contactResource'] = { 'contactName' : contact.strip(), 'email' : email.strip(), 'address' : re.sub(" 0 ", "", address).strip() }
                    elif 'metadata' in i:
                        str_splitted = i.split("|")
                        contact = email = address = ""
                        for j in range(len(str_splitted)):
                            if re.search("^[0-9]$", str_splitted[j]):
                                continue
                            if '@' in str_splitted[j]:
                                email = str_splitted[j]
                            elif j > 0 and j < 7 and 'metadata' not in str_splitted[j]:
                                contact = contact + " " + str_splitted[j]
                            elif j >= 7 and 'http' not in str_splitted[j]:
                                address = address + " " + str_splitted[j]
                        #metadata_detail['contactMetadata'] = { 'contactName' : contact.strip(), 'email' : email.strip(), 'address' : address.replace(" 0 ", "").replace("  0", "").strip() }
                        metadata_detail['contactMetadata'] = { 'contactName' : contact.strip(), 'email' : email.strip(), 'address' : re.sub(" 0 ", "", address).strip() }

            if 'legalConstraints' in current_metadata:
                if type(current_metadata['legalConstraints']) is str:
                    metadata_detail['legalConstraints'] = current_metadata['legalConstraints']
                if type(current_metadata['legalConstraints']) is list:
                    metadata_detail['legalConstraints'] = ", ".join(current_metadata['legalConstraints'])
            if 'crsDetails' in current_metadata:
                metadata_detail['crs'] = current_metadata['crsDetails']['name'] + " ("+current_metadata['crsDetails']['code']+":"+current_metadata['crsDetails']['codeSpace']+")"
            if 'spatialRepresentationType_text' in current_metadata:
                metadata_detail['refSys'] = current_metadata['spatialRepresentationType_text']
            if 'geoBox' in current_metadata:
                if current_metadata['category'].lower() == 'sos':
                    bbox = current_metadata['geoBox'].split("|")
                    metadata_detail['minLat'] = bbox[1]
                    metadata_detail['minLon'] = bbox[0]
                    metadata_detail['maxLat'] = str(float(bbox[3]) + 0.05)
                    metadata_detail['maxLon'] = str(float(bbox[2]) + 0.05)
                else:
                    bbox = current_metadata['geoBox'].split("|")
                    metadata_detail['minLat'] = bbox[1]
                    metadata_detail['minLon'] = bbox[0]
                    metadata_detail['maxLat'] = bbox[3]
                    metadata_detail['maxLon'] = bbox[2]
            if 'category' in current_metadata:
                metadata_detail['category'] = current_metadata['category']
            if 'abstract' in current_metadata:
                # expression_regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
                # urls = re.findall(expression_regex,current_metadata['abstract'])
                # print(urls)
                # for h in urls:
                #     if len(h) > 0:
                #         for j in h:                            
                #             if j != "":
                #                 print(j)
                #                 print('<a href="'+j+'">'+j+'</a>')
                #                 current_metadata['abstract'] = current_metadata['abstract'].replace(j, '<a href="'+j+'">'+j+'</a>')
                #     else:
                #         current_metadata['abstract'] = current_metadata['abstract'].replace(h, '<a href="'+h+'">'+h+'</a>')

                metadata_detail['abstract'] = current_metadata['abstract']
            if 'title' in current_metadata:
                metadata_detail['title'] = current_metadata['title']
            if 'keyword' in current_metadata:
                metadata_detail['keyword'] = ", ".join(current_metadata['keyword'])
            if 'lineage' in current_metadata:
                metadata_detail['lineage'] = current_metadata['lineage']
            if 'tempExtentBegin' in current_metadata:
                metadata_detail['tempExtentBegin'] = current_metadata['tempExtentBegin'].replace("t", " ").replace("z", "")
            if 'tempExtentEnd' in current_metadata:
                metadata_detail['tempExtentEnd'] = current_metadata['tempExtentEnd'].replace("t", " ").replace("z", "")
            if 'link' in current_metadata:
                if type(current_metadata['link']) is str:
                    link_split = current_metadata['link'].split('|')
                    metadata_detail['name_collection'] = link_split[0]
            if 'image' in current_metadata:
                thumbnail_split = current_metadata['image'].split("|")
                for e in thumbnail_split:
                    if 'http' in e or 'https' in e:
                        metadata_detail['thumbnail'] = e

            return metadata_detail
        else:
            #print(results)
            error = {}
            error['error'] = results
            return error
    except:
        error = {}
        error['error'] = "No metadata found"
        return error

def get_topic_list(request):
    url = "http://edp-portal.eurac.edu/geonetwork/srv/api/0.1/standards/iso19139/codelists/gmd%3AMD_TopicCategoryCode"
    results = requests.get(url, headers={"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", "Accept-Language": "q=0.9,en-US;q=0.8,en"})
    topic_list_str = JsonResponse(results.json()).content.decode("utf-8") 
    topic_list_dict = ast.literal_eval(topic_list_str)
    topic_list = []
    for t in topic_list_dict:
        if re.search(str(request.GET.get('term')), t):
            topic_list.append(topic_list_dict[t])
    return topic_list

def get_total_number_metadata(request, url_geometry_part):
    url = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&summaryOnly=1&"+url_geometry_part
    results = requests.get(url)
    summary_results = ast.literal_eval(JsonResponse(results.json(), safe=False).content.decode("utf-8"))
    #print(summary_results)
    if '@count' in str(summary_results):
        return (summary_results[0]['@count'])
    else:
        return(0)

def get_results_bounding_box(request, polygon, keyword=""):   
    tmp_results = {'metadata' : []}
    metadata_results = {'metadata' : []}
    c = 0
    polygon_str = ""

    print(polygon)

    for i in range(len(polygon)):
        for c in range(2):
            if float(polygon[i][c]) >= 0:
                polygon[i][c] = "+" + str(polygon[i][c])
            polygon_str = polygon_str + str(polygon[i][c])
        if i == len(polygon)-1:
            polygon_str = polygon_str
        else:
            polygon_str = polygon_str + ","
    #print(polygon_str)
    #url_geometry_part = "geometry=POLYGON((" + polygon[0]+polygon[1] + "," +  polygon[2]+polygon[3] + "," +  polygon[4]+polygon[5] + "," +  polygon[6]+polygon[7] + "," +  polygon[8]+polygon[9] + "))"
    url_geometry_part = "geometry=POLYGON((" + polygon_str + "))"
    #final_url = url_first_part + url_geometry_part + url_end_part

    total_number_metadata = get_total_number_metadata(request, url_geometry_part)
    #print(total_number_metadata)
    number_loop = int(int(total_number_metadata) / 100)
    #print("#loop "+str(number_loop))

    if (int(total_number_metadata)%100 > 0):
        for k in range(number_loop+1):
            url_first_part = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&any=" + keyword + "&bucket=s101&facet.q=&fast=index&from="+str((100*k)+1)+"&"
            url_end_part = "&relation=within_bbox&resultType=details&sortBy=title&sortOrder=reverse&to="+str((k+1)*100)
            final_url = url_first_part + url_geometry_part + url_end_part
            print(final_url)
            results = requests.get(final_url)
            current_results = ast.literal_eval(JsonResponse(results.json()).content.decode("utf-8"))            
            if 'metadata' in current_results:
                #print("current "+str(len(current_results['metadata'])))
                #print(current_results['metadata'])
                tmp_results['metadata'].append(current_results['metadata'])

    else:
        for k in range(number_loop):
            url_first_part = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&any=" + keyword + "&bucket=s101&facet.q=&fast=index&from="+str((100*k)+1)+"&"
            url_end_part = "&relation=within_bbox&resultType=details&sortBy=title&sortOrder=reverse&to="+str((k+1)*100)
            final_url = url_first_part + url_geometry_part + url_end_part
            print(final_url)
            results = requests.get(final_url)
            current_results = ast.literal_eval(JsonResponse(results.json()).content.decode("utf-8"))
            if 'metadata' in current_results:
                #print("current "+str(len(current_results['metadata'])))
                #print(current_results['metadata'])
                tmp_results['metadata'].append(current_results['metadata'])

    #print("metadata "+str(len(tmp_results['metadata'])))

    #print(tmp_results)
    #print(metadata_results)
    print(len(tmp_results['metadata']))

    if (len(tmp_results['metadata']) > 1):
        for h in range(len(tmp_results['metadata'])):
            #print(tmp_results['metadata'][h])
            print(h)
            metadata_results['metadata'] = metadata_results['metadata'] + tmp_results['metadata'][h]
    elif (len(tmp_results['metadata'])==1):
        metadata_results['metadata'] = tmp_results['metadata'][0]
    else:
        metadata_results['metadata'] = ['no results']
    
    #print("metadata "+str(len(metadata_results['metadata'])))
    #print(metadata_results['metadata'])

    if 'metadata' not in metadata_results:
        print('metadata not present')
        return "no results"

    return metadata_results['metadata']

def get_list_metadata_title(request):
    tmp_results = {'metadata' : []}
    results = requests.get("http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&summaryOnly=1")
    summary_results = ast.literal_eval(JsonResponse(results.json(), safe=False).content.decode("utf-8"))
    #print(summary_results)
    total_number_metadata = summary_results[0]['@count']
    metadata_title_item_list = []
    #print(total_number_metadata)
    number_loop = int(int(total_number_metadata) / 100)
    if (int(total_number_metadata)%100 > 0):
        for k in range(number_loop+1):
            url_first_part = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&bucket=s101&facet.q=&fast=index&from="+str((100*k)+1)
            url_end_part = "&resultType=details&sortBy=title&sortOrder=reverse&to="+str((k+1)*100)
            final_url = url_first_part + url_end_part
            print(final_url)
            results = requests.get(final_url)
            current_results = ast.literal_eval(JsonResponse(results.json()).content.decode("utf-8"))            
            if 'metadata' in current_results:
                #print("current "+str(len(current_results['metadata'])))
                #print(current_results['metadata'])
                tmp_results['metadata'].append(current_results['metadata'])

    else:
        for k in range(number_loop):
            url_first_part = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&bucket=s101&facet.q=&fast=index&from="+str((100*k)+1)
            url_end_part = "&resultType=details&sortBy=title&sortOrder=reverse&to="+str((k+1)*100)
            final_url = url_first_part + url_end_part
            print(final_url)
            results = requests.get(final_url)
            current_results = ast.literal_eval(JsonResponse(results.json()).content.decode("utf-8"))
            if 'metadata' in current_results:
                #print("current "+str(len(current_results['metadata'])))
                #print(current_results['metadata'])
                tmp_results['metadata'].append(current_results['metadata'])

    #print(len(tmp_results))
    #print(len(tmp_results['metadata']))
    keyword_search = str(request.GET.get('term'))
    #print(keyword_search)
    #print(tmp_results)
    print(len(tmp_results['metadata']))

    for i in range(len(tmp_results['metadata'])):
        for item in tmp_results['metadata'][i]:
            if re.search(keyword_search, item['title']):
                metadata_title_item_list.append(item['title'])
    return metadata_title_item_list

def get_results_by_keyword(request, keyword):
    tmp_results = {'metadata' : []}
    metadata_results = {'metadata' : []}
    c = 0
    results = requests.get("http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&summaryOnly=1")
    summary_results = ast.literal_eval(JsonResponse(results.json(), safe=False).content.decode("utf-8"))
    #print(summary_results)
    total_number_metadata = summary_results[0]['@count']
    #print(total_number_metadata)
    number_loop = int(int(total_number_metadata) / 100)
    #print("#loop "+str(number_loop))

    if (int(total_number_metadata)%100 > 0):
        for k in range(number_loop+1):
            url_first_part = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&any=" + keyword + "&bucket=s101&facet.q=&fast=index&from="+str((100*k)+1)
            url_end_part = "&resultType=details&sortBy=title&sortOrder=reverse&to="+str((k+1)*100)
            final_url = url_first_part + url_end_part
            print(final_url)
            results = requests.get(final_url)
            current_results = ast.literal_eval(JsonResponse(results.json()).content.decode("utf-8"))            
            if 'metadata' in current_results:
                #print("current "+str(len(current_results['metadata'])))
                #print(current_results['metadata'])
                tmp_results['metadata'].append(current_results['metadata'])

    else:
        for k in range(number_loop):
            url_first_part = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&any=" + keyword + "&bucket=s101&facet.q=&fast=index&from="+str((100*k)+1)
            url_end_part = "&resultType=details&sortBy=title&sortOrder=reverse&to="+str((k+1)*100)
            final_url = url_first_part + url_end_part
            print(final_url)
            results = requests.get(final_url)
            current_results = ast.literal_eval(JsonResponse(results.json()).content.decode("utf-8"))
            if 'metadata' in current_results:
                #print("current "+str(len(current_results['metadata'])))
                #print(current_results['metadata'])
                tmp_results['metadata'].append(current_results['metadata'])

    #print("metadata "+str(len(tmp_results['metadata'])))
    #print(len(tmp_results['metadata']))
    #print(tmp_results['metadata'])
    #if(len(tmp_results['metadata'])>1):

    #print(tmp_results)
    print(len(tmp_results['metadata']))
    if (len(tmp_results['metadata']) > 1):
        for h in range(len(tmp_results['metadata'])):
            #print(tmp_results['metadata'][h])
            metadata_results['metadata'] = metadata_results['metadata'] + tmp_results['metadata'][h]
    elif (len(tmp_results['metadata'])==1):
        metadata_results['metadata'] = tmp_results['metadata'][0]
    else:
        metadata_results['metadata'] = ['no results']

    #else:
    #    metadata_results['metadata'] + tmp_results['metadata'][0]
    #print("metadata "+str(len(metadata_results['metadata'])))
    #print(metadata_results['metadata'])

    if 'metadata' not in metadata_results:
        print('metadata not present')
        return "no results"

    return metadata_results['metadata']
