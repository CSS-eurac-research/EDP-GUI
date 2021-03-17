from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.http import JsonResponse
import requests
import json 
import ast, re
from .models import DocSource, SnippetCode


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

# class DiscoveryPageView(generic.ListView):
#     template_name = 'discovery.html'
#     context_object_name = 'topic_list'

def discovery(request):
    context = {}
    #print(request.body)
    if 'term' in request.GET:        
        return JsonResponse(get_topic_list(request), safe=False, status=200)
    
    context = {}
    if 'boundingbox' in str(request.body):
        polygon = json.loads(request.body)
        #print(polygon['boundingbox'])      
        metadata_results = get_results_bounding_box(request, polygon['boundingbox'])

        context = {
            'metadata_results': metadata_results,
        }
        return JsonResponse({'metadata_results': metadata_results}, safe=False, status=200)
        #return render(request, 'discovery.html', context)
    
    return render(request, 'discovery.html', context)
    
# def get_metadata_boundinbox(request):
#     context = {}
#     if 'boundingbox' in str(request.body):
#         polygon = json.loads(request.body)
#         #print(polygon['boundingbox'])      
#         metadata_results = get_results_bounding_box(request, polygon['boundingbox'])

#         context = {
#             'metadata_results': metadata_results,
#         }
#         #return JsonResponse(coords, safe=False)
#     return render(request, 'metadata_results.html', context)
    
def jupyter_page(request):
    return render(request, 'jupyter.html', {})

def openeo_page(request):
    return render(request, 'openeo.html', {})

def pgadmin_page(request):
    return render(request, 'pgadmin.html', {})

def maps_page(request):
    return render(request, 'maps.html', {})

def result_detail(request, uuid):
    url = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&_draft=y+or+n+or+e&_isTemplate=y+or+n&fast=index&uuid="+uuid
    #url = "http://edp-portal.eurac.edu/geonetwork/srv/api/0.1/records/"+uuid
    #print(url)
    results = requests.get(url, headers = {"Accept":"application/json;charset=utf-8", "content-type": "application/json;charset=utf-8"})
    #print(results)
    result_json_str = JsonResponse(results.json()).content.decode("utf-8") 
    result_json = ast.literal_eval(result_json_str)
    #print(result_json)
    result_json["metadata"]["keyword"] = ", ".join(result_json["metadata"]["keyword"])
    result_json["metadata"]["responsibleParty"] = result_json["metadata"]["responsibleParty"][0].replace("|", " ")
    #print(result_json["metadata"])  
     

    snippet_code_list = SnippetCode.objects.all()   

    context = {
        "uuid" : result_json["metadata"]["geonet:info"]["uuid"],
        "result_json" : result_json["metadata"],
        "snippet_code_list" : snippet_code_list
        #'title': result_json["metadata"]["title"],
    }
    return render(request, 'result_detail.html', context)

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
    return (summary_results[0]['@count'])

def get_results_bounding_box(request, polygon):   
    tmp_results = {'metadata' : []}
    metadata_results = {'metadata' : []}
    c = 0
    polygon_str = ""

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
            url_first_part = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&bucket=s101&facet.q=&fast=index&from="+str((100*k)+1)+"&"
            url_end_part = "&resultType=details&sortBy=title&sortOrder=reverse&to="+str((k+1)*100)
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
            url_first_part = "http://edp-portal.eurac.edu/geonetwork/srv/eng/q?_content_type=json&bucket=s101&facet.q=&fast=index&from="+str((100*k)+1)+"&"
            url_end_part = "&resultType=details&sortBy=title&sortOrder=reverse&to="+str((k+1)*100)
            final_url = url_first_part + url_geometry_part + url_end_part
            print(final_url)
            results = requests.get(final_url)
            current_results = ast.literal_eval(JsonResponse(results.json()).content.decode("utf-8"))
            if 'metadata' in current_results:
                #print("current "+str(len(current_results['metadata'])))
                #print(current_results['metadata'])
                tmp_results['metadata'].append(current_results['metadata'])

    #print("metadata "+str(len(tmp_results['metadata'])))

    for h in range(len(tmp_results['metadata'])):
        metadata_results['metadata'] = metadata_results['metadata'] + tmp_results['metadata'][h]
    
    #print("metadata "+str(len(metadata_results['metadata'])))
    #print(metadata_results['metadata'])

    if 'metadata' not in metadata_results:
        print('metadata not present')
        return "no metadata"

    return metadata_results['metadata']