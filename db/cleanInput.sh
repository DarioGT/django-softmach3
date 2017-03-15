rm t2 t3

# Sube las lineas q comienzan por mayusculas 
# sed -r ':a;N;$!ba;s/\n  `/ `/g'  t1 > t2
sed -r ':a;N;$!ba;s/\n(  `|\) ;)/ \1/g'  rai.sql > t2
sed -i 's/rai\./rai00base./g' t2
sed -i 's/rai_/rai00base_/g' t2
sed -i "s/[\\]\x27/ /g" t2

sed -i "s/protoLib_protodefinition/protoExt_viewdefinition/g" t2
sed -i "s/protoLib_customdefinition/protoExt_customdefinition/g" t2

sort -b t2 > t3 