$(document).ready(function() {
    let equipmentCounter = 0;
    let selectedClient = null;

    // Шаблон для оборудования
    function getEquipmentTemplate(index) {
        return `
        <div class="equipment-item" id="equipment-${index}">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0">Оборудование #${index + 1}</h6>
                <button type="button" class="btn btn-sm btn-danger remove-equipment" 
                        data-index="${index}">
                    <i class="bi bi-trash"></i> Удалить
                </button>
            </div>
            <div class="row">
                <div class="col-md-4">
                    <label class="form-label">Категория *</label>
                    <select class="form-select category-select" data-index="${index}">
                        <option value="">Выберите категорию</option>
                        {% for category in categories %}
                        <option value="{{ category.id }}">{{ category.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label">Бренд *</label>
                    <select class="form-select brand-select" data-index="${index}" disabled>
                        <option value="">Сначала выберите категорию</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label">Модель *</label>
                    <select class="form-select model-select" data-index="${index}" disabled>
                        <option value="">Сначала выберите бренд</option>
                    </select>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-4">
                    <label class="form-label">Серийный номер</label>
                    <input type="text" class="form-control serial-number" 
                           placeholder="Без номера">
                </div>
                <div class="col-md-4">
                    <label class="form-label">Инвентарный номер</label>
                    <input type="text" class="form-control inventory-number" 
                           placeholder="Опционально">
                </div>
                <div class="col-md-4">
                    <label class="form-label">Гарантия</label>
                    <select class="form-select equipment-guarantee">
                        <option value="DEFAULT">Без гарантии</option>
                        <option value="WARNING">Заводская гарантия</option>
                        <option value="DANGER">Гарантия сервисного центра</option>
                    </select>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-12">
                    <label class="form-label">Описание неисправности</label>
                    <textarea class="form-control defect-description" rows="2" 
                              placeholder="Со слов клиента..."></textarea>
                </div>
            </div>
        </div>`;
    }

    // Добавление оборудования
    $('#addEquipmentBtn').click(function() {
        const template = getEquipmentTemplate(equipmentCounter);
        $('#equipmentList').append(template);
        equipmentCounter++;
    });

    // Удаление оборудования
    $(document).on('click', '.remove-equipment', function() {
        const index = $(this).data('index');
        $(`#equipment-${index}`).remove();
    });

    // Загрузка брендов по категории
    $(document).on('change', '.category-select', function() {
        const index = $(this).data('index');
        const categoryId = $(this).val();
        const brandSelect = $(`.brand-select[data-index="${index}"]`);
        const modelSelect = $(`.model-select[data-index="${index}"]`);

        if (categoryId) {
            $.get('/api/brands/', {category_id: categoryId}, function(data) {
                brandSelect.empty();
                brandSelect.append('<option value="">Выберите бренд</option>');
                data.forEach(function(brand) {
                    brandSelect.append(`<option value="${brand.id}">${brand.name}</option>`);
                });
                brandSelect.prop('disabled', false);
                modelSelect.prop('disabled', true);
                modelSelect.empty();
                modelSelect.append('<option value="">Сначала выберите бренд</option>');
            });
        } else {
            brandSelect.prop('disabled', true);
            modelSelect.prop('disabled', true);
        }
    });

    // Загрузка моделей по бренду
    $(document).on('change', '.brand-select', function() {
        const index = $(this).data('index');
        const brandId = $(this).val();
        const modelSelect = $(`.model-select[data-index="${index}"]`);

        if (brandId) {
            $.get('/api/models/', {brand_id: brandId}, function(data) {
                modelSelect.empty();
                modelSelect.append('<option value="">Выберите модель</option>');
                data.forEach(function(model) {
                    modelSelect.append(`<option value="${model.id}">${model.full_name}</option>`);
                });
                modelSelect.prop('disabled', false);
            });
        } else {
            modelSelect.prop('disabled', true);
        }
    });

    // Поиск клиента
    $('#clientSearch').on('input', debounce(function() {
        const query = $(this).val();
        if (query.length >= 2) {
            $.get('/api/search-clients/', {q: query}, function(data) {
                const results = $('#clientResults');
                results.empty();

                if (data.length > 0) {
                    data.forEach(function(client) {
                        const item = `
                        <div class="card mb-2 client-item" data-client='${JSON.stringify(client)}'>
                            <div class="card-body py-2">
                                <h6 class="mb-1">${client.short_name}</h6>
                                <p class="mb-1 text-muted small">${client.contact_person}</p>
                                <p class="mb-0 text-muted small">${client.phone}</p>
                            </div>
                        </div>`;
                        results.append(item);
                    });
                    results.show();
                }
            });
        }
    }, 300));

    // Выбор клиента
    $(document).on('click', '.client-item', function() {
        const client = $(this).data('client');
        selectedClient = client;
        $('#clientSearch').val(client.short_name);
        $('#clientResults').hide();

        // Заполняем форму клиента
        $('#clientForm').html(`
            <div class="row">
                <div class="col-md-6">
                    <label class="form-label">Клиент</label>
                    <input type="text" class="form-control" value="${client.short_name}" readonly>
                    <input type="hidden" id="clientId" value="${client.id}">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Полное наименование</label>
                    <input type="text" class="form-control" value="${client.full_name}" readonly>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-6">
                    <label class="form-label">Ответственное лицо *</label>
                    <input type="text" class="form-control" id="actContactPerson" 
                           value="${client.contact_person}" required>
                </div>
                <div class="col-md-6">
                    <label class="form-label">Телефон *</label>
                    <input type="text" class="form-control" id="actContactPhone" 
                           value="${client.phone}" required>
                </div>
            </div>
        `);
    });

    // Переключение на нового клиента
    $('#newClientCheck').change(function() {
        if ($(this).is(':checked')) {
            $('#clientForm').hide();
            $('#newClientForm').show();
            selectedClient = null;
        } else {
            $('#newClientForm').hide();
            $('#clientForm').show();
        }
    });

    // Сохранение акта
    $('#saveActBtn').click(function() {
        // Собираем данные клиента
        let clientData = {};
        if ($('#newClientCheck').is(':checked')) {
            // Новый клиент
            clientData = {
                short_name: $('#shortName').val(),
                full_name: $('#fullName').val(),
                contact_person: $('#contactPerson').val(),
                phone: $('#phone').val(),
                email: $('#email').val(),
                address: $('#address').val()
            };
        } else if (selectedClient) {
            // Существующий клиент
            clientData = {
                id: selectedClient.id,
                contact_person: $('#actContactPerson').val(),
                phone: $('#actContactPhone').val()
            };
        } else {
            alert('Пожалуйста, выберите или создайте клиента');
            return;
        }

        // Собираем оборудование
        let equipmentList = [];
        $('.equipment-item').each(function(index) {
            const categoryId = $(this).find('.category-select').val();
            const brandId = $(this).find('.brand-select').val();
            const modelId = $(this).find('.model-select').val();

            if (!categoryId || !brandId || !modelId) {
                alert('Пожалуйста, заполните все обязательные поля для оборудования');
                return false;
            }

            equipmentList.push({
                model_id: modelId,
                serial_number: $(this).find('.serial-number').val() || 'Без номера',
                inventory_number: $(this).find('.inventory-number').val(),
                defect_description: $(this).find('.defect-description').val(),
                guarantee_type: $(this).find('.equipment-guarantee').val()
            });
        });

        if (equipmentList.length === 0) {
            alert('Пожалуйста, добавьте хотя бы одно оборудование');
            return;
        }

        // Собираем все данные
        const formData = {
            client: clientData,
            contact_person: $('#newClientCheck').is(':checked') ?
                $('#contactPerson').val() : $('#actContactPerson').val(),
            contact_phone: $('#newClientCheck').is(':checked') ?
                $('#phone').val() : $('#actContactPhone').val(),
            guarantee_type: $('#guaranteeType').val(),
            equipment_list: equipmentList
        };

        // Отправляем данные
        $.ajax({
            url: '{% url "create_reception_act" %}',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    $('#actNumber').text(response.act_number);
                    $('#successModal').modal('show');
                } else {
                    alert('Ошибка: ' + response.error);
                }
            },
            error: function() {
                alert('Произошла ошибка при сохранении акта');
            }
        });
    });

    // Функция для debounce
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Добавляем первое оборудование при загрузке
    $('#addEquipmentBtn').click();
});