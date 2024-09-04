from django.shortcuts import render, redirect
from .forms import PublicKeyForm
from .utils.yadisk_client import YandexDiskClient
from django.http import HttpResponse, Http404
import os
import requests
import zipfile
import io
from django.http import StreamingHttpResponse
import urllib.parse
from django.core.cache import cache


def home(request):
    if request.method == 'POST':
        form = PublicKeyForm(request.POST)
        if form.is_valid():
            public_key = form.cleaned_data['public_key']
            request.session['public_key'] = public_key
            return redirect('file_list')
    else:
        form = PublicKeyForm()
    return render(request, 'home.html', {'form': form})


def file_list(request):
    public_key = request.session.get('public_key')
    if not public_key:
        return redirect('home')

    cache_key = f'file_list_cache_{public_key}'

    resources = cache.get(cache_key)

    if not resources:
        client = YandexDiskClient(public_key)
        try:
            resources = client.get_resources()
            cache.set(cache_key, resources, timeout=600)
        except requests.HTTPError as e:
            return render(request, 'error.html', {'message': 'Не удалось получить ресурсы. Проверьте публичную ссылку.'})

    items = resources.get('_embedded', {}).get('items', [])

    file_type = request.GET.get('file_type')
    if file_type:
        if file_type == 'document':
            items = [item for item in items if item.get('type') == 'file' and item.get(
                'mime_type', '').startswith('application')]
        elif file_type == 'image':
            items = [item for item in items if item.get(
                'type') == 'file' and item.get('mime_type', '').startswith('image')]

    return render(request, 'file_list.html', {'items': items})


def download_file(request):
    file_url = request.GET.get('file_url')
    file_name = request.GET.get('file_name')

    if not file_url or not file_name:
        raise Http404("Файл не найден")

    client = YandexDiskClient(public_key=request.session.get('public_key'))

    def stream_file():
        try:
            with client.stream_file(file_url) as response_stream:
                for chunk in response_stream.iter_content(8192):
                    if chunk:
                        yield chunk
        except requests.HTTPError:
            raise Http404("Не удалось скачать файл")

    safe_file_name = urllib.parse.quote(file_name)

    response = StreamingHttpResponse(
        stream_file(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{safe_file_name}'
    return response


def download_multiple_files(request):
    if request.method == 'POST':
        file_urls = request.POST.getlist('file_urls')
        if not file_urls:
            return redirect('file_list')

        client = YandexDiskClient(public_key=request.session.get('public_key'))

        def zip_stream():
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_url in file_urls:
                    try:
                        file_name = urllib.parse.unquote(
                            os.path.basename(file_url))

                        with client.stream_file(file_url) as response_stream:
                            file_data = b''
                            for chunk in response_stream.iter_content(8192):
                                if chunk:
                                    file_data += chunk
                            zip_file.writestr(file_name, file_data)
                    except requests.HTTPError:
                        continue

            zip_buffer.seek(0)
            return zip_buffer

        zip_buffer = io.BytesIO()

        response = StreamingHttpResponse(
            zip_stream(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="files.zip"'
        return response
    else:
        raise Http404
