# coding: utf-8
import os
import suds
import time
import base64
import urllib
import io
import base64
import sys
import datetime

ANTIPLAGIAT_URI = "https://testapi.antiplagiat.ru"

# Создать клиента сервиса(https)
LOGIN = "testapi@antiplagiat.ru"
PASSWORD = "testapi"
COMPANY_NAME = "testapi"
APICORP_ADDRESS = "api.antiplagiat.ru:44902"
client = suds.client.Client("https://%s/apiCorp/%s?singleWsdl" % (APICORP_ADDRESS, COMPANY_NAME),
                            username=LOGIN,
                            password=PASSWORD)

import logging
logging.basicConfig(level=logging.INFO)
# logging.getLogger("suds.client").setLevel(logging.DEBUG)
# logging.getLogger("suds.transport").setLevel(logging.DEBUG)
# logging.getLogger("suds.xsd.schema").setLevel(logging.DEBUG)
# logging.getLogger("suds.wsdl").setLevel(logging.DEBUG)

# Подготовка описания загружаемого файла.
def get_doc_data(filename):
    data = client.factory.create("DocData")
    data.Data = base64.b64encode(open(filename, "rb").read()).decode()
    data.FileName = os.path.splitext(filename)[0]
    data.FileType = os.path.splitext(filename)[1]
    data.ExternalUserID = "ivanov"
    return data

# Пример самого распространенного сценария проверки документа.
def simple_check(filename):
    print("SimpleCheck filename=" + filename)
    # Описание загружаемого файла
    data = get_doc_data(filename)

    docatr = client.factory.create("DocAttributes")
    personIds = client.factory.create("PersonIDs")
    personIds.CustomID = "original"

    arr = client.factory.create("ArrayOfAuthorName")

    author = client.factory.create("AuthorName")
    author.OtherNames = "Иван Иванович"
    author.Surname = "Иванов"
    author.PersonIDs = personIds

    arr.AuthorName.append(author) 
    
    docatr.DocumentDescription.Authors = arr

    # Загрузка файла
    try:
        uploadResult = client.service.UploadDocument(data, docatr)
    except Exception:
        raise

    # Идентификатор документа. Если загружается не архив, то список загруженных документов будет состоять из одного элемента.
    id = uploadResult.Uploaded[0].Id

    try:
        # Отправить на проверку с использованием всех подключеных компании модулей поиска
        client.service.CheckDocument(id)
		# Отправить на проверку с использованием только собственного модуля поиска и модуля поиска "wikipedia". Для получения списка модулей поиска см. пример get_tariff_info()
		#client.service.CheckDocument(id, ["wikipedia", COMPANY_NAME])
    except suds.WebFault:
        raise

    # Получить текущий статус последней проверки
    status = client.service.GetCheckStatus(id)

    # Цикл ожидания окончания проверки
    while status.Status == "InProgress":
        time.sleep(status.EstimatedWaitTime*0.1)
        status = client.service.GetCheckStatus(id)

    # Проверка закончилась не удачно.
    if status.Status == "Failed":
        print(u"При проверке документа %s произошла ошибка: %s" % (filename, status.FailDetails))

    # Получить краткий отчет
    report = client.service.GetReportView(id)

    print("Report Summary: %0.2f%%" % (report.Summary.Score,))
    for checkService in report.CheckServiceResults:
        # Информация по каждому поисковому модулю
        print("Check service: %s, Score.White=%0.2f%% Score.Black=%0.2f%%" %
                (checkService.CheckServiceName,
                 checkService.ScoreByReport.Legal, checkService.ScoreByReport.Plagiarism))
        if not hasattr(checkService, "Sources"):
            continue
        for source in checkService.Sources:
            # Информация по каждому найденному источнику
            print('\t%s: Score=%0.2f%%(%0.2f%%), Name="%s" Author="%s" Url="%s"' %
                (source.SrcHash, source.ScoreByReport, source.ScoreBySource,
                 source.Name, source.Author, source.Url))

    # Получить полный отчет
    options = client.factory.create("ReportViewOptions")
    options.FullReport = True
    options.NeedText = True
    options.NeedStats = True
    options.NeedAttributes = True
    fullreport = client.service.GetReportView(id, options)
    if fullreport.Details.CiteBlocks:
        # Найти самый большой блок заимствований и вывести его
        maxBlock = max(fullreport.Details.CiteBlocks, key=lambda x: x.Length)
        print(u"Max block length=%s Source=%s text:\n%s..." % (maxBlock.Length, maxBlock.SrcHash,
               fullreport.Details.Text[maxBlock.Offset:maxBlock.Offset + min(maxBlock.Length, 200)]))
			   
    print(u"Author Surname=%s OtherNames=%s CustomID=%s" % (fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].Surname,
		fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].OtherNames,
		fullreport.Attributes.DocumentDescription.Authors.AuthorName[0].PersonIDs.CustomID))

def incorrect_upload(filename):
    print("IncorrectUpload filename=" + filename)
    # Описание загружаемого файла
    data = client.factory.create("DocData")
    data.Data = base64.b64encode(open(filename).read())
    data.FileName = os.path.splitext(filename)[0]
    data.FileType = ".tre"

    # Загрузка файла
    try:
        uploadResult = client.service.UploadDocument(data)
    except suds.WebFault as e:
        if e.fault.faultcode == "a:InvalidArgumentException":
            # Данный файл не может быть загружен. Конкреnная причина указана в поле Message.
            # Повторять вызов с теми же параметрами бессмыслено, результат будет тот же.
            raise Exception(u"Загрузка файла не возможна: " + e.fault.faultstring)
        raise
        # Проблема не связана с конкретным файлом имеет смысл повторить попытку позже

# Перебор всех полученных отчетов
def enumerate_reports():
    print("Enumerate Reports")
    # Выбрать документы пользователя с идентификатором во внешней системе "ivanov"
    opts = client.factory.create("EnumerateReportsOptions")
    opts.ExternalUserID = "ivanov"
    opts.Count = 10
    opts.Skip = 0
    # Получить первую пачку отчетов, сортировка всегда обратная хронологическая, отчет последнего загруженного документа будет первым
    reps = client.service.EnumerateReportInfos(opts)
    # Счетчик отчетов
    i = 0
    # Функция EnumerateReportInfos возвращает результаты проверки пачками. Пустая пачка означает, что перебор завершился.
    while (reps and len(reps) > 0):
        for info in reps:
            i += 1
            print("%d  DocName: %s\n   Status: %s" % (i, info.DocumentInfo.Attributes.Name, info.CheckStatus.Status))
            if info.CheckStatus.Status == "Ready":
                print("   %s, %s" % (info.CheckStatus.Summary.Score, ANTIPLAGIAT_URI + info.CheckStatus.Summary.ReportWebId))
        # Получить следующую пачку отчетов
        opts.Skip = i
        reps = client.service.EnumerateReportInfos(opts)

# Перебор всех загруженных документов
def enumerate_documents():
    print("Enumerate Documents")
    # Получить первую пачку документов
    docs = client.service.EnumerateDocuments(None)
    # Счетчик документов
    i = 0
    # Функция EnumerateDocuments возвращает идентификаторы пачками. Пустая пачка означает, что перебор завершился.
    while (docs and len(docs) > 0):
        for id in docs:
            i += 1
            # Каждый пятый документ добавляем в индекс
            if (i % 5) == 0:
                client.service.SetIndexState(id, "Indexed")

            # Каждому третьему добавляем атрибут
            if (i % 3) == 0:
                docnum = client.factory.create("CustomAttribute")
                docnum.AttrName = "docnum"
                docnum.AttrValue = str(i)
                docatr = client.factory.create("DocAttributes")
                docatr.Custom = [docnum]

                client.service.UpdateDocumentAttributes(id, docatr)

        # Получить следующую пачку идентификаторов документов
        docs = client.service.EnumerateDocuments(docs[-1])

    print("Total documents count: %s (%s)" % (i, client.service.GetCompanyStats().TotalCount))

# Перебор всех документов добавленных в индекс
def enumerate_index():
    print("EnumerateIndex")
    # При вызове EnumerateDocuments в опциях указывается, что требуются только документы добавленные в индекс
    enumerateOptions = client.factory.create("EnumerateDocumentsOptions")
    enumerateOptions.AddedToIndex = True
    docs = client.service.EnumerateDocuments(None, enumerateOptions)
    # Счетчик документов
    i = 0
    # Функция EnumerateDocuments возвращает идентификаторы пачками. Пустая пачка означает, что перебор завершился.
    while (docs and len(docs) > 0):
        for id in docs:
            i += 1
            # Каждый второй документ удаляем из индекса
            if (i % 2) == 0:
                client.service.SetIndexState(id, "None")
        # Получить следующую пачку идентификаторов документов
        docs = client.service.EnumerateDocuments(docs[-1], enumerateOptions)

    print("Total indexed documents count: %s (%s)" % (i, client.service.GetCompanyStats().AddedToIndexCount))

# Проверить документ, получить ссылку на отчет на сайте "Antiplagiat"
def get_web_report(filename):
    # Описание загружаемого файла
    data = get_doc_data(filename)

    # Загрузка файла
    uploadResult = client.service.UploadDocument(data)

    # Идентификатор документа. Если загружается не архив, то список загруженных документов будет состоять из одного элемента.
    id = uploadResult.Uploaded[0].Id
    # Отправить на проверку с использованием всех подключеных компании модулей поиска
    client.service.CheckDocument(id)

    # Отправить на проверку с использованием только собственного модуля поиска и модуля поиска "wikipedia". Для получения списка модулей поиска см. пример get_tariff_info()
	#client.service.CheckDocument(id, ["wikipedia", COMPANY_NAME])

    # Получить текущий статус последней проверки
    status = client.service.GetCheckStatus(id)

    # Цикл ожидания окончания проверки
    while status.Status == "InProgress":
        time.sleep(status.EstimatedWaitTime)
        status = client.service.GetCheckStatus(id)

    # Проверка закончилась не удачно.
    if status.Status == "Failed":
        print("При проверке документа %s произошла ошибка: %s" % (filename, status.FailDetails))
        return

    # Получить ссылку на полный отчет на сайте "Антиплагиат"
    print("Full Report: " + ANTIPLAGIAT_URI + status.Summary.ReportWebId)

    # Получить ссылку на краткий отчет на сайте "Антиплагиат"
    print("Short Report: " + ANTIPLAGIAT_URI + status.Summary.ShortReportWebId)

    # Получить ссылку на отчет только для чтения на сайте "Антиплагиат"
    print("Readonly Report: " + ANTIPLAGIAT_URI + status.Summary.ReadonlyReportWebId)

# Методы для работы с папками
def folders_methods(filename1, filename2):
    print("folders_methods")

    email = "testapi@antiplagiat.ru"

    # Пользователь создаёт папку "New Folder"
    folderId = client.service.AddFolder(email, "New folder")

    # Пользователь переименовывает её в "Documents"
    client.service.RenameFolder(email, folderId, "Documents")

    # Описание параметров добавления папки
    folderOptions = client.factory.create("FolderOptions")
    folderOptions.ParentId = folderId

    # Пользователь создаёт в папке "Documents" новую папку "Important"
    importantFolderId = client.service.AddFolder(email, "Important", folderOptions)

    # Описание первого загружаемого файла
    data1 = get_doc_data(filename1)

    # Описание параметров загрузки первого загружаемого файла
    uploadOptions1 = client.factory.create("UploadOptions")
    uploadOptions1.FolderId = folderId
    uploadOptions1.FromUser = email

    # Пользователь загружает в папку "Documents" файл fileName1
    client.service.UploadDocument(data1, None, uploadOptions1)

    # Описание второго загружаемого файла
    data2 = get_doc_data(filename2)

    # Описание параметров загрузки второго загружаемого файла
    uploadOptions2 = client.factory.create("UploadOptions")
    uploadOptions2.FolderId = folderId
    uploadOptions2.FromUser = email

    # Пользователь загружает в папку "Important" файл fileName2
    client.service.UploadDocument(data2, None, uploadOptions2)

    # Пользователь создаёт папку "Trash"
    trashFolderId = client.service.AddFolder(email, "Trash")

    # Описание параметров перечисления документов
    enumerateDocumentsOptions1 = client.factory.create("EnumerateDocumentsOptions")
    enumerateDocumentsOptions1.FromUser = email

    # Пользователь получает идентификаторы всех своих документов
    docIds = client.service.EnumerateDocuments(None, enumerateDocumentsOptions1)

    # Пользователь перемещает свои документы в папку "Trash"
    client.service.MoveDocuments(email, trashFolderId, docIds)

    # Пользователь получает дерево папок
    folderTree = client.service.GetFolders(email)

    print("FolderTree:")

    print("\nTop level:")
    print("Name: %s" % (folderTree.Name))

    print("\nNext level:")

    for folder in folderTree.Children[0]:
        print("Name: %s" % (folder.Name))

    print("\nGet documents from \"Trash\"")

    # Описание параметров перечисления документов
    enumerateDocumentsOptions2 = client.factory.create("EnumerateDocumentsOptions")
    enumerateDocumentsOptions2.InStorage = False
    enumerateDocumentsOptions2.FolderId = trashFolderId
    enumerateDocumentsOptions2.FromUser = email

    # Пользователь получает свои документы из папки "Trash"
    trashDocs = client.service.EnumerateDocuments(None, enumerateDocumentsOptions2)

    print("Documents count: %s" % (len(trashDocs)))

    # Пользователь удаляет папки "Documents" и "Trash"
    client.service.DeleteFolder(email, folderId)
    client.service.DeleteFolder(email, trashFolderId)

# Методы для работы с хранилищем
def storage_methods(filename1, filename2):
    print("storage_methods")

    # Пользователь создаёт папку "New Folder" в хранилище
    folderId = client.service.AddFolder(None, "New folder")

    # Пользователь переименовывает её в "Documents"
    client.service.RenameFolder(None, folderId, "Documents")

    # Описание параметров добавления папки
    folderOptions = client.factory.create("FolderOptions")
    folderOptions.ParentId = folderId

    # Пользователь создаёт в папке "Documents" новую папку "Important"
    importantFolderId = client.service.AddFolder(None, "Important", folderOptions)

    # Описание первого загружаемого файла
    data1 = get_doc_data(filename1)

    # Описание параметров загрузки первого загружаемого файла
    uploadOptions1 = client.factory.create("UploadOptions")
    uploadOptions1.FolderId = folderId
    uploadOptions1.ToStorage = True

    # Пользователь загружает в папку "Documents" файл fileName1
    client.service.UploadDocument(data1, None, uploadOptions1)

    # Описание второго загружаемого файла
    data2 = get_doc_data(filename2)

    # Описание параметров загрузки второго загружаемого файла
    uploadOptions2 = client.factory.create("UploadOptions")
    uploadOptions2.FolderId = folderId
    uploadOptions2.ToStorage = True

    # Пользователь загружает в папку "Important" файл fileName2
    client.service.UploadDocument(data2, None, uploadOptions2)

    # Пользователь создаёт папку "Trash" в хранилище
    trashFolderId = client.service.AddFolder(None, "Trash")

    # Пользователь получает идентификаторы всех документов из хранилища
    enumerateDocumentsOptions = client.factory.create("EnumerateDocumentsOptions")
    enumerateDocumentsOptions.InStorage = True
    docIds = client.service.EnumerateDocuments(None, enumerateDocumentsOptions)

    # Пользователь перемещает все документы в папку "Trash"
    client.service.MoveDocuments(None, trashFolderId, docIds)

    # Пользователь получает дерево папок хранилища
    folderTree = client.service.GetFolders(None)

    print("FolderTree:")

    print("\nTop level:")
    print("Name: %s" % (folderTree.Name))

    print("\nNext level:")

    for folder in folderTree.Children[0]:
        print("Name: %s" % (folder.Name))

    print("\nGet documents from \"Trash\"")

    # Описание параметров перечисления документов
    enumerateDocumentsOptions2 = client.factory.create("EnumerateDocumentsOptions")
    enumerateDocumentsOptions2.InStorage = True
    enumerateDocumentsOptions2.FolderId = trashFolderId

    # Пользователь получает документы хранилища из папки "Trash"
    trashDocs = client.service.EnumerateDocuments(None, enumerateDocumentsOptions2)

    print("Documents count: %s" % (len(trashDocs)))

    # Пользователь удаляет папки "Documents" и "Trash"
    client.service.DeleteFolder(None, folderId)
    client.service.DeleteFolder(None, trashFolderId)

# Получение информации о текущем тарифе
def get_tariff_info():
    print("GetTariffInfo")

    # Получить информацию о текущем тарифе
    tariffInfo = client.service.GetTariffInfo()

    print("Tariff name: %s" % (tariffInfo.Name))
    print("Tariff subscription date: %s" % (tariffInfo.SubscriptionDate))
    print("Tariff expiration date: %s" % (tariffInfo.ExpirationDate))
    print("Tariff total checks count: %s" % (tariffInfo.TotalChecksCount))
    print("Tariff remained checks count: %s" % (tariffInfo.RemainedChecksCount))

    print("\nAvailable check services:")

    for checkService in tariffInfo.CheckServices[0]:
        print("%s (%s)" % (checkService.Code, checkService.Description))

# Проверить документ, получить ссылку на pdf-версию отчета на сайте "Antiplagiat"
def export_report_to_pdf(filename):
    print("export_report_to_pdf")

    # Описание загружаемого файла
    data = get_doc_data(filename)

    # Загрузка файла
    try:
        uploadResult = client.service.UploadDocument(data)
    except Exception:
        raise

    # Идентификатор документа.  Если загружается не архив, то список
    # загруженных документов будет состоять из одного элемента.
    id = uploadResult.Uploaded[0].Id

    try:
        # Отправить на проверку с использованием всех подключеных компании модулей поиска
        client.service.CheckDocument(id)
		# Отправить на проверку с использованием только собственного модуля поиска и модуля поиска "wikipedia". Для получения списка модулей поиска см. пример get_tariff_info()
		#client.service.CheckDocument(id, ["wikipedia", COMPANY_NAME])
    except Exception:
        raise

    # Получить текущий статус последней проверки
    status = client.service.GetCheckStatus(id)

     # Цикл ожидания окончания проверки
    while status.Status == "InProgress":
        time.sleep(max(status.EstimatedWaitTime, 10) * 0.1)
        status = client.service.GetCheckStatus(id)

    # Проверка закончилась не удачно.
    if status.Status == "Failed":
        print("При проверке документа %s произошла ошибка: %s" % (filename, status.FailDetails))

    # Запросить формирование последнего полного отчета в формат PDF.
    exportReportInfo = client.service.ExportReportToPdf(id)

    while exportReportInfo.Status == "InProgress":
        time.sleep(max(exportReportInfo.EstimatedWaitTime, 10) * 0.1)
        exportReportInfo = client.service.ExportReportToPdf(id)

    # Формирование отчета закончилось неудачно.
    if exportReportInfo.Status == "Failed":
        print("При формировании PDF-отчета для документа %s произошла ошибка: %s" % (filename, exportReportInfo.FailDetails))

    # Получить ссылку на отчет на сайте "Антиплагиат"
    # ВНИМАНИЕ! Не гарантируется что данная ссылка будет работать вечно, она может перестать работать в любой момент,
    # поэтому нельзя давать ее пользвателю. Нужно скачивать pdf себе и дальше уже управлять его временем жизни
    downloadLink = ANTIPLAGIAT_URI + exportReportInfo.DownloadLink
    print("PDF full report (number = %s): %s" % (exportReportInfo.ReportNum, downloadLink))

    # Опции для формирования краткого отчета с номером 1 в формат PDF.
    options = client.factory.create("ExportReportOptions")
    options.ReportNum = 1
    options.ShortReport = True

    # Запросить формирование отчета в формат PDF с указанными опциями.
    exportReportInfo = client.service.ExportReportToPdf(id, options)

    # Цикл ожидания формирования отчета
    while exportReportInfo.Status == "InProgress":
        time.sleep(max(exportReportInfo.EstimatedWaitTime, 10) * 0.1)
        exportReportInfo = client.service.ExportReportToPdf(id, options)

    # Формирование отчета закончилось неудачно.
    if exportReportInfo.Status == "Failed":
        print("При формировании PDF-отчета для документа %s произошла ошибка" % (filename))

    # Получить ссылку на отчет на сайте "Антиплагиат"
    # ВНИМАНИЕ! Не гарантируется что данная ссылка будет работать вечно, она может перестать работать в любой момент,
    # поэтому нельзя давать ее пользвателю. Нужно скачивать pdf себе и дальше уже управлять его временем жизни
    downloadLink = ANTIPLAGIAT_URI + exportReportInfo.DownloadLink
    print("PDF short report (number = %s): %s" % (exportReportInfo.ReportNum, downloadLink))

# Пример получения справки по проверенному файлу
def get_verification_report(filename):
    print("get_verification_report")

    # Описание загружаемого файла
    data = get_doc_data(filename)

    # Загрузка файла
    uploadResult = client.service.UploadDocument(data)

    # Идентификатор документа. Если загружается не архив, то список загруженных документов будет состоять из одного элемента.
    id = uploadResult.Uploaded[0].Id

    # Отправить на проверку с использованием всех подключеных компании модулей поиска
    client.service.CheckDocument(id)
	# Отправить на проверку с использованием только собственного модуля поиска и модуля поиска "wikipedia". Для получения списка модулей поиска см. пример get_tariff_info()
	#client.service.CheckDocument(id, ["wikipedia", COMPANY_NAME])

    # Получить текущий статус последней проверки
    status = client.service.GetCheckStatus(id)

    # Цикл ожидания окончания проверки
    while status.Status == "InProgress":
        time.sleep(status.EstimatedWaitTime)
        status = client.service.GetCheckStatus(id)

    # Проверка закончилась не удачно.
    if status.Status == "Failed":
        print("При проверке документа %s произошла ошибка: %s" % (filename, status.FailDetails))
        return

    try:
        #Выгрузить справку можно c заполненными полями или без
        # Для заполнения полей необходимо создать объект опций справки с желаемыми значениями свойств
        reportOptions = client.factory.create("VerificationReportOptions")
        reportOptions.Author = u"Иванов И.И." # ФИО автора работы
        reportOptions.Department = u"Факультет общей и прикладной физики" # Факультет (структурное подразделение)
        reportOptions.ShortReport = True # Требуется ли ссылка на краткий отчёт? (qr код)
        reportOptions.Type = u"Дипломная работа" # Тип работы
        reportOptions.Verifier = u"Петров П.П." # ФИО проверяющего
        reportOptions.Work = u"Когерентная спиновая динамика двумерного электронного газа"  # Название работы

        # С заполнением полей
        reportWithFields = client.service.GetVerificationReport(id, reportOptions)
        # Без заполнения полей
        # reportWithoutFields = client.service.GetVerificationReport(id)

        # Запись в файл
        decoded = base64.b64decode(reportWithFields)
        fileName = get_report_name(id, reportOptions)
        f = open(fileName, 'wb')
        f.write(decoded)
    except suds.WebFault as e:
        if e.fault.faultcode == "a:InvalidArgumentException":
            raise Exception(u"У документа нет отчёта/закрытого отчёта или в качестве id в GetVerificationReport передано None: " + e.fault.faultstring)
        if e.fault.faultcode == "a:DocumentIdException":
            raise Exception(u"Указан невалидный DocumentId" + e.fault.faultstring)
        raise
        # Проблема не связана с передаваемыми параметрами, имеет смысл повторить попытку позже


def get_report_name(id, reportOptions):
    author = u''

    if reportOptions is not None:
        if reportOptions.Author:
            author = '_' + reportOptions.Author

    curDate = datetime.datetime.today().strftime('%Y%m%d')
    return u'Certificate_%s_%s%s.pdf' % (id.Id, curDate, author)

# Сценарий проверки на самоцитирование.
def selfcite_check(filename):
    print("SelfCiteCheck filename=" + filename)
    # Описание загружаемого файла
    data = get_doc_data(filename)

    docatr = client.factory.create("DocAttributes")
    personIds = client.factory.create("PersonIDs")
    personIds.CustomID = "original"

    arr = client.factory.create("ArrayOfAuthorName")

    author = client.factory.create("AuthorName")
    author.OtherNames = "Иван Иванович"
    author.Surname = "Иванов"
    author.PersonIDs = personIds

    arr.AuthorName.append(author)
    
    docatr.DocumentDescription.Authors = arr
    opts = client.factory.create("UploadOptions")
    opts.AddToIndex = True

    # Загрузка файла
    try:
        uploadResult = client.service.UploadDocument(data, docatr, opts)
    except Exception:
        raise

    # Идентификатор документа. Если загружается не архив, то список загруженных документов будет состоять из одного элемента.
    id = uploadResult.Uploaded[0].Id

    try:
        # Отправить на проверку с использованием всех подключеных компании модулей поиска
        client.service.CheckDocument(id)
    except suds.WebFault:
        raise

    # Получить текущий статус последней проверки
    status = client.service.GetCheckStatus(id)

    # Цикл ожидания окончания проверки
    while status.Status == "InProgress":
        time.sleep(status.EstimatedWaitTime*0.1)
        status = client.service.GetCheckStatus(id)

    # Проверка закончилась не удачно.
    if status.Status == "Failed":
        print(u"При проверке документа %s произошла ошибка: %s" % (filename, status.FailDetails))
		
    # Загрузка файла
    try:
        uploadResult = client.service.UploadDocument(data, docatr)
    except Exception:
        raise

    # Идентификатор документа. Если загружается не архив, то список загруженных документов будет состоять из одного элемента.
    idSelfCite = uploadResult.Uploaded[0].Id

    try:
        # Отправить на проверку с использованием всех подключеных компании модулей поиска
        client.service.CheckDocument(idSelfCite)
    except suds.WebFault:
        raise

    # Получить текущий статус последней проверки
    status = client.service.GetCheckStatus(idSelfCite)

    # Цикл ожидания окончания проверки
    while status.Status == "InProgress":
        time.sleep(status.EstimatedWaitTime*0.1)
        status = client.service.GetCheckStatus(idSelfCite)
		

    # Получить краткий отчет
    report = client.service.GetReportView(idSelfCite)
	#Должно быть полное самоцитирование
    print("Report SelfCite: %0.2f%%" % (report.Summary.DetailedScore.SelfCite))


# simple_check("test_wiki.pdf")
# enumerate_documents()
# incorrect_upload("test_wiki.pdf")
# enumerate_index()
# get_web_report(r"test_wiki.pdf")
# folders_methods("test_wiki.pdf", "test_wiki.pdf")
# storage_methods("test_wiki.pdf", "test_wiki.pdf")
# export_report_to_pdf("test_wiki.pdf")
# get_tariff_info()
# get_verification_report("test_wiki.pdf")
# enumerate_reports()
# selfcite_check("test_wiki.pdf")
