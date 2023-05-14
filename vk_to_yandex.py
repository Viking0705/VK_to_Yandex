import requests
import json

from datetime import datetime
from tqdm import tqdm

class VkDownloader:    
    def __init__(self, user_id, token):
        self.params = {
            'owner_id': user_id,
            'album_id': 'profile',
            'access_token': token,
            'v': '5.131',
            'count': '5',
            'extended': '1'
            }
    
    def get_fotos_vk(self):
        URL = 'https://api.vk.com/method/photos.get'
        data = requests.get(URL, params=self.params).json()
        return data
    
    def foto_info(self, data):
        # control_dict: вспомогательный словарь со всеми размерами фото vk
        #  для поиска максимального размера конкретного фото
        control_dict = {'s': 1, 'm': 2, 'o': 3, 'p': 4, 'q': 5,
                        'r': 6, 'x': 7,'y': 8, 'z': 9, 'w': 10}
        
        # словарь count_likes_dict: ключи - количество лайков,
        # значения - у скольких фото оно повторяется
        count_likes_dict = {}
        size_dict = {}
        list_foto = []
        
        for item in data['response']['items']:
            # чищу словарь с размерами фотографии
            # для работы с новой фотографией
            size_dict.clear()

            # определяю код размера,
            # который для данного фото максимальный (max_size)
            for size in item['sizes']:
                size_dict[size ['type']] = control_dict[size ['type']]
            max_size = max(size_dict.items(), key=lambda x: x[1])[0]

            # заполняю список list_files данными о фото,
            #  которые будем загружать на Yandex Disk
            for size in item['sizes']:
                likes = item['likes']['count']
                date = datetime.fromtimestamp(item['date'])
                if size ['type'] == max_size:

                    # заполняю словарь с подсчётом количества лайков
                    # на фото count_likes_dict: ключ-количество лайков,
                    # значение-количество фото с таким числом лайков
                    if likes in count_likes_dict.keys():
                        count_likes_dict[likes] += 1
                    else:
                        count_likes_dict[likes] = 1
            
                    list_foto.append({"size": max_size,
                                      "url": size ['url'],
                                      "likes": likes, 
                                      "date": date.strftime('%Y_%m_%d %H.%M.%S')})
    
            # определяю названия фото в зависимости от количества лайков:
            # если совпадёт, то в название добавляю дату и время загрузки фото
            for foto in list_foto:
                if count_likes_dict[foto['likes']] > 1:
                    foto['foto_name'] = str(foto['likes']) + ' __ '\
                    + str(foto['date']) + '.jpg'
                else:
                    foto['foto_name'] = str(foto['likes']) + '.jpg'

        return list_foto


class YaUploader:    
    def __init__(self, token):
        self.token = token
    
    def __headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {self.token}'
        }

    def create_folder(self,path):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {"path": path}
        response = requests.put(url=url, headers=self.__headers(), params=params)
        return response.status_code

    
    def download_files(self, path_folder, url_vk):
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        params = {"path": path_folder, 'url': url_vk}
        response = requests.post(url=url, headers=self.__headers(), params=params)
        return response.status_code
       


if __name__ == '__main__':
    def write_to_json(list_foto):
        data = []
        for foto in list_foto:
            data.append({"file_name": foto['foto_name'],
                        "size": foto['size']})
        with open('data.json', 'w') as outfile:
            json.dump(data, outfile, indent=2)
    
    def vk_user_id(user_id_vk):
        if user_id_vk.isdigit():
            return user_id_vk
        else:
            photo_link = input('Вероятно, пользователь использует короткое имя в качестве ID. \
Пожалуйста, введите ссылку на любую его фотографию: ')
            return photo_link.partition('photo')[2].partition('_')[0]
        
    # Получаю токены Яндекс и VK из файла
    with open('D:/my_doc/tok.txt', 'r') as f:
        token_yandex = str(f.readline().strip())
        token_vk = str(f.readline().strip())

    # работа с VK (получение фото)
    user_id_vk = vk_user_id(input('Введите id пользователя vk: '))
    downloader = VkDownloader(user_id_vk, token_vk)
    downloader.params['count'] = input('Введите количество скачиваемых фото: ')
    data = downloader.get_fotos_vk()
    list_foto = downloader.foto_info(data)
    if len(list_foto) < int(downloader.params['count']):
        print(f"В профиле пользователя меньше {downloader.params['count']} \
фото. Будет загружено {len(list_foto)} фото")

    # работа с YandexDisk (загрузка фото)
    path_folder_ya= str(datetime.now().strftime('%Y_%m_%d %H.%M.%S'))
    uploader = YaUploader(token_yandex)
    result = uploader.create_folder(path_folder_ya)

    print('Загружаем фото на Яндекс Диск:')
    for foto in tqdm(list_foto):
        path_ya_foto = path_folder_ya + '/' + foto['foto_name']   
        url_vk = foto['url']
        result = uploader.download_files(path_ya_foto, url_vk)

    # создание json-файла
    write_to_json(list_foto)
