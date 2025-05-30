# Импорт библиотек
from __future__ import absolute_import
from __future__ import print_function

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torch.backends.cudnn as cudnn

import torchvision
import torchvision.transforms as transforms

import os
import argparse
import matplotlib.pyplot as plt
from PIL import Image
import PIL
import random
import numpy as np

from src.utils import pattern_craft, mask_craft, embed_backdoor

# Аргументы командной строки

parser = argparse.ArgumentParser(description='PyTorch Backdoor Attack Crafting')
parser.add_argument('--out_dir', default='attack4',
                    type=str, help='output direction')


args = parser.parse_args()


device = 'cuda' if torch.cuda.is_available() else 'cpu'

random.seed()
out_dir = args.out_dir

# Переменные атакованных изображений и меток

test_images_attacks = None
test_labels_attacks = None
train_images_attacks = None
train_labels_attacks = None

# Параметры атаки - число атакуемых классов и изображений

NC = 10

NUM_OF_ATTACKS = 500

# Загрузка данных из набора

print('Подготовка данных...')
transform_train = transforms.Compose([
        transforms.ToTensor(),
    ])

transform_test = transforms.Compose([
        transforms.ToTensor(),
    ])

trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform_train)
testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform_test)

# Паттерн и маска проводимых атак

pattern = pattern_craft(trainset.__getitem__(0)[0].size())
mask = mask_craft(pattern)

# Внедрение случайного числа бэкдоров в отдельно взятый класс (SC - истинный класс изображения, TC - целевой)

SC = 3
TC = 9

# for SC in range(10):
#    TC = (SC + 1)%10
# Создание обучающих изображений с бэкдорами
ind_train = [i for i, label in enumerate(trainset.targets) if label==SC]
ind_train = np.random.choice(ind_train, NUM_OF_ATTACKS, False)
for i in ind_train:
    if train_images_attacks is not None:
        train_images_attacks = torch.cat([train_images_attacks, embed_backdoor(trainset.__getitem__(i)[0], pattern, mask).unsqueeze(0)], dim=0)
        train_labels_attacks = torch.cat([train_labels_attacks, torch.tensor([TC], dtype=torch.long)], dim=0)
    else:
        train_images_attacks = embed_backdoor(trainset.__getitem__(i)[0], pattern, mask).unsqueeze(0)
        train_labels_attacks = torch.tensor([TC], dtype=torch.long)

# Создание тестовых изображений с бэкдорами
ind_test = [i for i, label in enumerate(testset.targets) if label==SC]

for i in ind_test:
    if test_images_attacks is not None:
        test_images_attacks = torch.cat([test_images_attacks, embed_backdoor(testset.__getitem__(i)[0], pattern, mask).unsqueeze(0)], dim=0)
        test_labels_attacks = torch.cat([test_labels_attacks, torch.tensor([TC], dtype=torch.long)], dim=0)
    else:
        test_images_attacks = embed_backdoor(testset.__getitem__(i)[0], pattern, mask).unsqueeze(0)
        test_labels_attacks = torch.tensor([TC], dtype=torch.long)

# Сохранение образцов в папку
if not os.path.isdir(out_dir):
    os.mkdir(out_dir)
train_attacks = {'image': train_images_attacks, 'label': train_labels_attacks}
test_attacks = {'image': test_images_attacks, 'label': test_labels_attacks}

torch.save(train_attacks, './' + out_dir + '/train_attacks')
torch.save(test_attacks, './' + out_dir + '/test_attacks')
torch.save(ind_train, './' + out_dir + '/ind_train')
torch.save(pattern, './' + out_dir + '/pattern')

# Запись информации об атаке

f = open('./' + out_dir + '/attack_info.txt', "w")
f.write('Изначальный класс: ' + str(SC) + '. Новый класс: ' + str(TC))
f.close()
