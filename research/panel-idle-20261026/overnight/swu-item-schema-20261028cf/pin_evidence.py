#!/usr/bin/env python3
"""Read pinned local ELF and write static metadata in this owned directory."""
import hashlib,json
from pathlib import Path
import inspect_core as c
root=Path(__file__).resolve().parent
factory_path=root.parent/'swu-header-validation-20261027bx/descriptor-factory.json'
factory=json.loads(factory_path.read_text())
fields={
1:'u32 item_id; u8 item_type_raw; u64 original_size; u64 processed_size; bytes16 optional_string; children',
2:'u32 group_id; children',7:'children',10:'bytes8 string',11:'bytes8 string',
14:'bytes8 salt; u64 processed_size',16:'u32 public_key_id; bytes16 signature',18:'u32 crc32',19:'u32 group_id',
21:'bytes8 first_string; bytes8 second_string',25:'bytes8 first_string; bytes8 optional_string; i16 field_50; i16 field_54',
35:'bytes8 first_string; bytes8 second_string',53:'bytes8 string; bytes32 vector; i16 field_40; i16 field_44',
55:'u64 field_1c_wire; children',56:'u64 field_1c_wire; u32 field_20; bytes8 string; children',
57:'u32 field_1c; u64 processed_size',58:'children',59:'bytes8 first_string; bytes16 optional_string; bytes8 third_string',
60:'bytes8 string; bytes32 vector; i16 field_40; i16 field_44; u32 field_48',61:'bytes8 string',62:'u32 count; repeated(u16,u16)'}
anchors=[
('original_size_to_graph_A0',0x29e66c,0x14),('original_size_getter',0x2aa34c,8),
('graph_A0_size_getter',0x356be4,8),('graph_A0_size_setter',0x356c94,8),
('original_size_into_partition_location',0x1eceee,0x18),('bounded_partition_location_ctor_call',0x1ecf4a,0x10),
('same_location_into_write_action',0x1ed1be,0x44),('same_location_into_verify_action',0x1ed234,0x38),
('verify_action_retains_location',0x1f54ce,0x10),('verify_action_location_read_source',0x1f4a4a,0x16),
('partition_location_read_stream_vtable',0x4b9ccc,0x1c),
('scoped_read_length_from_location',0x203f6a,0x1c),('scoped_read_zero_position_and_bound',0x203fa2,0x20),
('scoped_read_remaining_length_cap',0x18f2aa,0x36),('scoped_read_exact_EOF',0x18f254,0x14),
('final_decoded_stream_original_size_cap',0x1fd328,0x18),('final_decoded_stream_bound_store',0x1fd39e,0x10),
('verify_expected_CRC_read',0x1ffb6a,0x16),('verify_completed_CRC_complement_compare',0x1ffb9c,0x1e),
('first_CRC_descriptor_to_expected',0x235978,0x2c),('expected_CRC_getter',0x234c8c,4),
('CRC_sink_type_string',0x3abc1c,123),('reflected_CRC_byte_feed',0x109ea2,0x18),
('CRC_sink_callback_pair',0x1ff116,0x1e),('verify_source_dispatch',0x1fbe7c,0x20),
('CRC_sink_callback_construct',0x1fd080,0x14),('CRC_sink_all_ones_state',0x1fcfd8,0x5c),
('RSA_before_AES_before_optional_XZ',0x236a60,0x18),
('two_candidate_word_initialization',0x1d6150,0x44),('candidate_copy_and_end',0x1d6196,0x20),
('candidate_iteration_begin',0x1d6450,4),('candidate_iteration_step',0x1d68f0,14),
('candidate_hash_to_RSA_constructor',0x1d66f6,16),('successful_candidate_out_copy',0x1d6a6e,14),
 ('RSA_descriptor_key_ID_dump_label',0x2a716a,18),('RSA_descriptor_key_ID_label_string',0x40ab2c,16),
 ('payload_key_ID_compared_to_PEM_CRC',0x2363c6,18),('payload_RSA_uses_inherited_hash_word',0x2363e8,32),
('caller_header_crypto_record',0x198192,12),('same_record_to_graph_builder',0x1981d0,16),
('graph_builder_preserves_crypto_r3',0x29c384,6),('graph_builder_crypto_setter',0x29c5d2,10),
('graph_crypto_set_get',0x3502ac,0x28),('graph_clone_crypto_copy',0x3522a8,16),
('graph_to_pipeline_caller',0x1fd26a,0x46),('pipeline_crypto_record_copy',0x236958,0x18),
('AES_graph_builder',0x29cda8,0x32),('AES_graph_salt_size_getters',0x359558,12),
('section_crypto_factory_argument_setup',0x235112,0x4a),('factory_direction_conversion',0x243178,0x24),
('item_id_read',0x2aa892,0x10),('item_type_read',0x2aa690,0x10),
('item_original_size_read',0x2aa6b0,0x16),('item_processed_size_read',0x2aa8f4,0x14),
('item_string16_length_read',0x2aa914,0x10),('item_child_count_read',0x2aaa0a,0x12),
('group_id_and_count_read',0x2a3858,0x30),
('image_version_string8_read',0x2a8396,0x24),('image_version_optional_string8_read',0x2a83c6,0x20),
('image_version_signed16_pair_read',0x2a8204,0x32),
('BDiff_vector32_length_read',0x2ad766,0x10),('BDiff_signed16_pair_read',0x2ad522,0x32),
('MultiBDiff_extra_u32_read',0x2ae62c,0x14),
('secure_downgrade_u64_read',0x2a50a0,16),('secure_downgrade_child_count_read',0x2a50b0,0x10),
('wildcard_u32_read',0x2a62f2,0x12),('wildcard_string8_length_read',0x2a6304,0x1c),
('postpone_optional_string16_read',0x2b0354,0x1c),('postpone_third_string8_read',0x2b03a8,0x1c),
('XZ_fields_read',0x2aed5a,0x34),('base_version_pair_count_read',0x2b1200,0x20),
]
result={'core_path':str(c.CORE),'core_bytes':len(c.raw),'core_sha256':c.EXPECTED,
 'factory_sha256':hashlib.sha256(factory_path.read_bytes()).hexdigest(),
 'field_notation':'all LE; bytesN=uN byte length then bytes; children=u32 count then u8 presence+optional framed descriptor',
 'factory_layouts':[{'tag':d['tag'],'serializer':d['candidates'][0]['serializer'],'fields_after_mandatory':fields[d['tag']]} for d in factory],
 'header_candidate_order':[{'mode':1,'keySize':2,'derive':1,'rsa_hash_algorithm':2},{'mode':1,'keySize':0,'derive':0,'rsa_hash_algorithm':0}],
 'anchors':[{'claim':claim,'address':hex(a),'bytes':n,'hex':c.read(a,n).hex()} for claim,a,n in anchors]}
(root/'schema-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'factory_tags':len(factory),'byte_anchors':len(anchors),'core_sha256':c.EXPECTED}))
