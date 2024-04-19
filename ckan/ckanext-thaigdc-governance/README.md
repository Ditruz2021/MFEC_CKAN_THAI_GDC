# ckanext-thaigdc_governance

Thaigdc_governance Extension พัฒนาขึ้นเพื่อเป็นส่วนหนึ่งของ CKAN Open-D เพื่อเพิ่มความสามารถให้ระบบบัญชีข้อมูลหน่วยงาน (Agency Data Catalog) สามารถสนับสนุนการดำเนินงานตาม [กรอบธรรมาภิบาลข้อมูลภาครัฐ](https://www.dga.or.th/policy-standard/standard/dga-005/dga-006/) โดยมีความสามารถเพิ่มเติมที่สำคัญ ได้แก่  

- รองรับผู้ใช้งานในบทบาทบริกรข้อมูล (data steward)  
- รองรับ workflow การตรวจสอบและรับรองชุดข้อมูลก่อนการเผยแพร่  
- รองรับ workflow การขอใช้ข้อมูล (data request) ภายในหน่วยงาน  
- รองรับการกำหนดระดับชั้นข้อมูลของชุดข้อมูล 5 ระดับ ได้แก่  เปิดเผย เผยแพร่ภายในองค์กร ลับ ลับมาก ลับที่สุด (อ้างอิง: [มาตรฐานสำนักงานพัฒนารัฐบาลดิจิทัล (องค์การมหาชน) ว่าด้วยหลักเกณฑ์การจัดระดับชั้นและการแบ่งปันข้อมูลภาครัฐ (GOVERNMENT DATA CLASSIFICATION AND DATA SHARING FRAMEWORK) (มสพร. 8-2565)](https://standard.dga.or.th/dga-std/5343/))  
- รองรับการควบคุมสิทธิ์ในการเข้าถึงชุดข้อมูลตามระดับชั้นข้อมูลของชุดข้อมูล  

ทั้งนี้ผู้ใช้ที่เป็นเจ้าของข้อมูลสามารถจัดการนำเข้า ปรับปรุง และส่งเรื่องพิจารณาเผยแพร่ชุดข้อมูลต่อบริกรข้อมูล (data steward) ตามกระบวนการพิจารณาคุณภาพ หมวดหมู่และระดับชั้นข้อมูลของหน่วยงาน เมื่อชุดข้อมูลได้รับการอนุมัติให้เผยแพร่แล้ว ผู้ใช้ข้อมูลจะได้รับสิทธิ์ในการเข้าถึง สืบค้น ร้องขอ และใช้ประโยชน์ชุดข้อมูลตามที่หน่วยงานกำหนดไว้ โดยศึกษาการใช้งานได้ที่ [คู่มือการใช้งาน](https://gitlab.nectec.or.th/opend/ckanext-thaigdc_governance/-/raw/bd9f383082d11c00323c5a7b12faf0f33b95f42e/CKAN-Open-D_data_governance_manual.pdf)


## Requirements

ใช้สำหรับ CKAN 2.9.5 เท่านั้น (ที่ติดตั้งโดยใช้ Python 2.x) โดยจำเป็นต้องติดตั้ง Extension [ckanext-thai_gdc 2.0.0](https://gitlab.nectec.or.th/opend/installing-ckan/-/blob/master/ckan-extension-2.0.0.md) ก่อน


## การติดตั้ง (Installation)


1. install extension โดยทำตามคำสั่ง ดังนี้
```sh
source /usr/lib/ckan/default/bin/activate

cd /usr/lib/ckan/default

pip install -e 'git+https://gitlab.nectec.or.th/opend/ckanext-thaigdc_governance.git#egg=ckanext-thaigdc_governance'
```

2. Activate extension และ กำหนด user sysadmin โดยแก้ไขไฟล์ config ของ CKAN ดังนี้:
```sh
sudo vi /etc/ckan/default/ckan.ini
```
    - ckan.plugins (วางไว้หน้า thai_gdc)
        > ckan.plugins = ... thaigdc_governance thai_gdc ...
    - thaigdc_governance.admin_user = ใส่ username sysadmin
    - thaigdc_governance.datasteward_groupmail = ใส่ group email ของทีมบริกรข้อมูล (ถ้ามี)
```sh
sudo supervisorctl reload
```

3. คำสั่งในการสร้างหน่วยงานสำหรับทีมบริกรข้อมูล "คณะกรรมการธรรมาภิบาลข้อมูล/ทีมบริกรข้อมูล" และ migrate ชุดข้อมูลเดิมในระบบ (ในกรณีที่มีชุดข้อมูลอยู่แล้ว) ดังนี้
```sh
source /usr/lib/ckan/default/bin/activate

cd /usr/lib/ckan/default
     
sudo /usr/lib/ckan/default/bin/ckan --config=/etc/ckan/default/ckan.ini governance init

sudo supervisorctl reload
```

4. ทดสอบการเข้าถึงระบบส่วนของบริกรข้อมูล โดยล็อกอินในระบบ CKAN เป็นผู้ดูแลระบบ จากนั้นเรียกไปที่ URL '[hostname]/governance' หากสามารถเข้าถึงหน้าดังกล่าว แสดงว่าไม่มีปัญหาในการติดตั้ง


### การตั้งค่าเพิ่มเติม


การกำหนดสิทธิ์ให้ผู้ใช้ที่เป็นบริกรข้อมูล  
- ล็อคอินเป็นผู้ดูแลระบบใน CKAN จากนั้นเลือกองค์กร "ทีมบริกรข้อมูล" เลือกเพิ่มสมาชิก จากนั้นเลือกผู้ใช้ที่จะกำหนดให้เป็นบริกรข้อมูล (data steward) ของหน่วยงาน โดยกำหนดสิทธิ์ของผู้ใช้นั้นเป็น บรรณาธิการ (Editor) ในหน่วยงาน "ทีมบริกรข้อมูล" ([hostname]/organization/data-steward-committee) ที่สร้างโดยอัตโนมัติจากข้อ 3.  
- ผู้ใช้ที่ได้รับสิทธิ์เป็นบริกรข้อมูล สามารถทดลองเรียกไปที่ URL '[hostname]/governance' หากสามารถเข้าถึงหน้าดังกล่าว แสดงว่าได้รับสิทธิ์เรียบร้อยแล้ว

### หมายเหตุ  
- การติดตั้งจะมีผลให้ชุดข้อมูลทุกชุดที่มีอยู่เดิมอยู่ในสถานะอนุมัติให้เผยแพร่แล้ว (approved) และถูกกำหนดระดับชั้นของข้อมูลตั้งต้นให้โดยอัตโนมัติ โดยชุดข้อมูลที่มีสถานะ public จะกำหนดระดับชั้นเป็น "เปิดเผย" และ ชุดข้อมูลที่มีสถานะ private จะกำหนดระดับชั้นเป็น "เผยแพร่ในองค์กร" อย่างอัตโนมัติ
- การถอนการติดตั้งจำเป็นทำตามขั้นตอนในหัวข้อการถอนการติดตั้ง (Uninstallation) ถ้ามีชุดข้อมูลที่ยังไม่ได้รับการอนุมัติให้เผยแพร่ จะมีผลให้ชุดข้อมูลดังกล่าวถูกลบออกจากระบบอย่างอัตโนมัติ ลบรายการคำขอใช้ข้อมูลทั้งหมด และลบฟิลด์ระดับชั้นข้อมูลออกจากทุกชุดข้อมูล
- ซอฟต์แวร์นี้อยู่ในระดับ beta version ที่อาจมีการปรับปรุงและเปลี่ยนแปลงได้ในอนาคต การนำไปใช้งานกับระบบที่ใช้ปฎิบัติงานจริง จึงควรพิจารณาให้แน่ใจก่อนว่าจะสามารถตอบโจทย์ความต้องการทำงานของหน่วยงานได้จริงก่อนการนำไปใช้งาน


## การถอนการติดตั้ง (Uninstallation)

1. uninstall extension โดยทำตามคำสั่ง ดังนี้
```sh
source /usr/lib/ckan/default/bin/activate

cd /usr/lib/ckan/default
     
sudo /usr/lib/ckan/default/bin/ckan --config=/etc/ckan/default/ckan.ini governance clear
```

2. Deactivate extension โดยแก้ไขไฟล์ config ของ CKAN ดังนี้:
```sh
sudo vi /etc/ckan/default/ckan.ini
```
    - ลบ 'thaigdc_governance' ออกจากรายการใน ckan.plugins
```sh
sudo supervisorctl reload
```
3. Rebuild Index:
```sh
/usr/lib/ckan/default/bin/ckan -c /etc/ckan/default/ckan.ini search-index rebuild -r
```

# วิธีติดตั้งแบบ Docker
สำหรับติดตั้งแบบ Docker จะมี 2 กรณีคือ กรณีที่ต้องการติดตั้งใหม่ และ กรณีที่ต้องอัพเดท thai_gdc เดิมให้เป็น thaigdc_governance 

1. กรณีติดตั้ง docker thaigdc_governance ใหม่
  - ดาวน์โหลด ckan-docker-thai-gdc
  ```
  git clone https://gitlab.nectec.or.th/opend/ckan-docker-thai-gdc.git ~/ckan-docker
  ```
  - สร้างไฟล์ .env จากไฟล์ .env.template ที่เตรียมไว้ให้
  ```
  cd ~/ckan-docker
  cp .env.template .env
  ```
  - แก้ไขไฟล์ .env
  ``` 
  vi .env
  ```
  ```
    - กำหนด Password สำหรับ Database ของ CKAN
        > POSTGRES_PASSWORD={ckan_password}
    - กำหนด Password สำหรับ Datastore
        > DATASTORE_READONLY_PASSWORD={datastore_password}
    - กำหนดชื่อ Host สำหรับ Database Postgres
        > POSTGRES_HOST=db
    - กำหนด version ของ CKAN (แก้ไขเป็น 2.9)
        > CKAN_VERSION=2.9
    - ตัวเลขกำกับ container (default)
        > PROJECT_NUMBER=1
    - กำหนด port สำหรับ Nginx (แก้ไขเป็น 80)
        > NGINX_PORT=80
    - กำหนด port สำหรับ Datapusher
        > DATAPUSHER_PORT=8800
    - กำหนด url สำหรับเว็บ (แก้ไขเป็น IP หรือ Domain)
        > DEFAULT_URL=http://{IP or Domain}
    - กำหนด CKAN Site ID (default)
        > CKAN_SITE_ID=default
    - กำหนด CKAN Port
        > CKAN_PORT=5000
    - กำหนดรายละเอียด SysAdmin ของระบบ
        > CKAN_SYSADMIN_NAME={admin_username}
        > CKAN_SYSADMIN_PASSWORD={admin_password}
        > CKAN_SYSADMIN_EMAIL={admin_email}
    - url สำหรับเชื่อมต่อกับ solr
        > CKAN_SOLR_URL=http://solr:8983/solr/ckan
    - url สำหรับเชื่อมต่อกับ redis
        > CKAN_REDIS_URL=redis://redis:6379/0
    - path สำหรับ storage ของ CKAN
        > CKAN__STORAGE_PATH=/var/lib/ckan
    - plugin ทั้งหมดที่เปิดใช้งาน
        > CKAN__PLUGINS=envvars discovery search_suggestions thaigdc_governance thai_gdc stats opendstats image_view text_view recline_view resource_proxy webpage_view datastore xloader noregistration scheming_datasets pdf_view hierarchy_display hierarchy_form dcat dcat_json_interface structured_data
    - default view
        > CKAN__VIEWS__DEFAULT_VIEWS=image_view text_view recline_view webpage_view pdf_view
    - อนุญาตให้ผู้ใช้อัพโหลดไฟล์ที่กำหนด
        > CKAN__UPLOAD__USER__MIMETYPES=image/png image/jpg image/gif
    - เพิ่ม user sysadmin ของระบบ
        > CKAN___THAIGDC_GOVERNANCE__ADMIN_USER={admin_username}
    - จำเป็นต้องตั้งค่า SMTP Server ของหน่วยงาน
        > CKAN_SMTP_SERVER=smtp.corporateict.domain:25
        > CKAN_SMTP_STARTTLS=True
        > CKAN_SMTP_USER=user
        > CKAN_SMTP_PASSWORD=pass
        > CKAN_SMTP_MAIL_FROM=ckan@localhost
  ```
  - แก้ไขไฟล์ docker-compose.yml
  ```
    ในส่วนของ ckan service ในแก้ไขบรรทัด
    image: thepaeth/ckan-thai_gdc:ckan-${CKAN_VERSION}-xloader
    เป็น
    image: thepaeth/ckan-thaigdc_governance:v1.0.0
  ```
  - เริ่มการทำงานของ docker
  ```
  docker-compose up -d --build

  # ตรวจการทำงานของ docker-compose ที่ทำการ run อยู่ หลังจากนั้นรอประมาณ 15 วินาที
  docker ps
  ```

2. กรณีอัพเดท thai_gdc เดิมให้เป็น thaigdc_governance
  - ไปยัง path ที่ clon ckan-docker มา เช่น
  ```
  cd ~/ckan-docker
  ```
  - แกัไขไฟล์ .env ดังนี้
  ```
  vi .env
    - plugin ทั้งหมดที่เปิดใช้งาน
        > CKAN__PLUGINS=envvars discovery search_suggestions thaigdc_governance thai_gdc stats opendstats image_view text_view recline_view resource_proxy webpage_view datastore xloader noregistration scheming_datasets pdf_view hierarchy_display hierarchy_form dcat dcat_json_interface structured_data
    - อนุญาตให้ผู้ใช้อัพโหลดไฟล์ที่กำหนด
        > CKAN__UPLOAD__USER__MIMETYPES=image/png image/jpg image/gif
    - เพิ่ม user sysadmin ของระบบ
        > CKAN___THAIGDC_GOVERNANCE__ADMIN_USER={admin_username}
    - จำเป็นต้องตั้งค่า SMTP Server ของหน่วยงาน
        > CKAN_SMTP_SERVER=smtp.corporateict.domain:25
        > CKAN_SMTP_STARTTLS=True
        > CKAN_SMTP_USER=user
        > CKAN_SMTP_PASSWORD=pass
        > CKAN_SMTP_MAIL_FROM=ckan@localhost
  ```
  - แก้ไขไฟล์ docker-compose.yml
  ```
    ในส่วนของ ckan service ในแก้ไขบรรทัด
    image: thepaeth/ckan-thai_gdc:ckan-${CKAN_VERSION}-xloader
    เป็น
    image: thepaeth/ckan-thaigdc_governance:v1.0.0
  ```
  - เริ่มการทำงานของ docker
  ```
  docker-compose up -d ckan

  # ตรวจการทำงานของ docker-compose ที่ทำการ run อยู่ หลังจากนั้นรอประมาณ 15 วินาที
  docker ps
  ```